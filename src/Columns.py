import re
import typing
import fnmatch
from enum import IntEnum
from sqlparse import tokens as Token


class StorageTypes(IntEnum):
    NULL = 0  # this value because it amuses me
    INTEGER = 1
    TEXT = 2
    REAL = 3
    BLOB = 4
    # Types in SQLite3: https://www.sqlite.org/datatype3.html
    # Flexible typing is a feature of SQLite, not a bug.
    # Update: As of version 3.37.0 (2021-11-27), SQLite provides STRICT tables that do rigid type enforcement,
    # for developers who prefer that kind of thing.
    #       TODO add support for strict tables?
    # SQLite recognizes the keywords "TRUE" and "FALSE", as of version 3.23.0 (2018-04-02) but those keywords
    # are really just alternative spellings for the integer literals 1 and 0 respectively.
    #
    #       TODO support for dates as special cases of the storage types - text-date, real-data, int-date?
    # SQLite does not have a storage class set aside for storing dates and/or times. Instead, the built-in Date
    # And Time Functions of SQLite are capable of storing dates and times as TEXT, REAL, or INTEGER values:
    #   * TEXT as ISO8601 strings ("YYYY-MM-DD HH:MM:SS.SSS").
    #   * REAL as Julian day numbers, the number of days since noon in Greenwich on November 24, 4714 B.C.
    #     according to the proleptic Gregorian calendar.
    #   * INTEGER as Unix Time, the number of seconds since 1970-01-01 00:00:00 UTC.
    # Storage Types => null, integer, real, text, blob
    # For tables not declared as STRICT, the affinity of a column is determined by the declared type of the
    # column, according to the following rules in the order shown:
    #   1) If the declared type contains the string "INT" then it is assigned INTEGER affinity.
    #   2) If the declared type of the column contains any of the strings "CHAR", "CLOB", or "TEXT" then that
    #      column has TEXT affinity. Notice that the type VARCHAR contains the string "CHAR" and is thus
    #      assigned TEXT affinity.
    #   3) If the declared type for a column contains the string "BLOB" or if no type is specified then the
    #      column has affinity BLOB.
    #   4) If the declared type for a column contains any of the strings "REAL", "FLOA", or "DOUB" then the
    #      column has REAL affinity.
    #   5) Otherwise, the affinity is NUMERIC.
    # Note that the order of the rules for determining column affinity is important. A column whose declared
    # type is "CHARINT" will match both rules 1 and 2 but the first rule takes precedence and so the column
    # affinity will be INTEGER.
    #   INTEGER
    #       INT
    #       INTEGER
    #       TINYINT
    #       SMALLINT
    #       MEDIUMINT
    #       BIGINT
    #       UNSIGNED BIG INT
    #       INT2
    #       INT8
    #   TEXT
    #       CHARACTER(X)
    #       VARCHAR(X)
    #       VARYING
    #       CHARACTER(X)
    #       NCHAR(X)
    #       NATIVE
    #       CHARACTER(X)
    #       NVARCHAR(X)
    #       TEXT
    #       CLOB
    #   BLOB
    #       BLOB
    #   REAL
    #       REAL
    #       DOUBLE
    #       DOUBLE PRECISION
    #       FLOAT
    # NUMERIC
    #       NUMERIC
    #       DECIMAL(X,Y)
    #       BOOLEAN
    #       DATE
    #       DATETIME
    #       STRING (not really, it's just how the rules work)


# TODO add support for unique/check/collate/generated constraints
class Column:
    """
    Representation of a column in the table.  Allows for consolidation of the validation functions and meta-data.
    The validation is performed through a single function which takes only the prospective value as an argument, and
    returns True if the value is good.  This defaults to a simple type check.
    """

    # region Properties
    @property
    def Name(self):
        return self._name

    @property
    def ColumnType(self):
        return self._rawType

    @property
    def Default(self):
        return self._default

    @Default.setter
    def Default(self, value):
        self._default = value

    @property
    def PrimaryKey(self) -> bool:
        return self._ispk

    @property
    def Nullable(self):
        return self._null

    @property
    def ForeignKey(self):
        return self._fk

    @property
    def IsForeignKey(self):
        return self._fk is not None

    @property
    def Unique(self) -> bool:
        return self._solo

    @property
    def IsValid(self) -> bool:
        return self._valid

    # endregion

    def __init__(self, name: str, props: str, toks: list = []):
        """
        Convert a string from the ini file with the column description into a column object.
        """
        self._name = name
        vdator = ''

        # find the parans enclosing the validator
        oparan = props.find('(')

        self._valid = True

        # exclude the validator and leave it hanging
        if oparan > 0:
            parts = props[:oparan].split(',')
            cparan = props.find(')', oparan)
            vdator = props[oparan:cparan]
        else:
            parts = props.split(',')

        # object field defaults
        self._rawType = parts[0].strip()  # column type will always be there
        self._null = True
        self._solo = False
        self._ispk = False
        self._fk = None
        self._default = None

        # match the column type to storage type
        if self._rawType.lower().find('int') >= 0:
            # SQLITE Rule1: If the declared type contains the string "INT" then it is assigned INTEGER affinity.
            self._storageT = StorageTypes.INTEGER
        elif self._rawType.lower().find('char') >= 0 \
                or self._rawType.lower().find('clob') >= 0 \
                or self._rawType.lower().find('text') >= 0:  # better way to do this than breaking across lines?
            # SQLITE Rule2: If the declared type of the column contains any of the strings "CHAR", "CLOB", or "TEXT"
            # then that column has TEXT affinity. Notice that the type VARCHAR contains the string "CHAR" and is thus
            # assigned TEXT affinity.
            self._storageT = StorageTypes.TEXT
            pass
        elif len(self._rawType) == 0 or self._rawType.lower().find("blob") >= 0:
            # SQLITE Rule3: If the declared type for a column contains the string "BLOB" or if no type is specified
            # then the column has affinity BLOB.
            self._storageT = StorageTypes.BLOB
        elif self._rawType.lower().find('real') >= 0 \
                or self._rawType.lower().find('floa') >= 0\
                or self._rawType.lower().find('doub') >= 0:
            # SQLITE Rule4: If the declared type for a column contains any of the strings "REAL", "FLOA", or "DOUB"
            # then the column has REAL affinity.
            self._storageT = StorageTypes.REAL
        else:
            # SQLITE Rule5: Otherwise, the affinity is NUMERIC.
            # This is a weird position - NUMERIC isn't actually a storage type, but rather is an internal mechanism for
            # the engine to manage more mixed scenarios.  TEXT provides the most flexibility, so it will be the type
            # used to simulate that.
            self._storageT = StorageTypes.TEXT

        # assign the validator
        if len(vdator) > 0:
            tech, func = vdator.split(':')
            if tech.strip(' ').lower() == 'regex':
                self._validator = lambda x: re.search(func.strip(), x) != None
            elif tech.strip(' ').lower() == 'math':
                func[0] = 'x'
                self._validator = lambda x: func.strip(' ')
        else:
            # default validators for the storage types
            match self._storageT:
                case StorageTypes.INTEGER:
                    self._validator = lambda val: isinstance(val, int) or val is None
                case StorageTypes.NULL:
                    self._validator = lambda val: val is None
                case StorageTypes.REAL:
                    self._validator = lambda val: isinstance(val, float) or val is None
                case StorageTypes.TEXT:
                    self._validator = lambda val: isinstance(val, str) or val is None
                case StorageTypes.BLOB:
                    self._validator = lambda val: True  # just let it ride
                case _:
                    self._validator = lambda val: True  # just let it ride

        propmap = {
            'required': 'not null',
            'key': 'primarykey',
            'unique': 'unique',
            'reference': 'foreignkey',
            'default': 'default'
        }

        for p in parts[1:]:
            p1 = p.strip().lower()
            match p1:
                case 'required':
                    self._null = False  # equivalent of not null
                case 'unique':
                    self._solo = True
                case 'key':
                    if self._fk is not None:
                        raise ValueError(f"{name}: Cannot be both foreign and primary key")
                    self._valid &= 'primarykey' in toks if len(toks) > 0 else self._valid

                    # side effects of being PK
                    self._ispk = True
                    self._null = False  # equivalent of not null
                case p1 if p1.startswith('reference'):
                    if self._ispk:
                        raise ValueError(f"{name}: Cannot be both foreign and primary key")

                    # parse the reference and save to fk
                    pp = p.strip().split(' ')
                    if len(pp) == 2:
                        self._fk = pp[1]
                    else:
                        # error! expect 'reference <table>.<col>' - found extra spaces
                        pass
                # TODO adjust for expressions - compile/convert to python and store as lambda?
                case p1 if p1.startswith('default'):
                    # extract the default and pass it in
                    pp = p.strip().split(' ')
                    if len(pp) == 2:
                        # need to change the type based on the column type
                        match self._storageT:
                            case StorageTypes.INTEGER:
                                self._default = int(pp[1])
                            case StorageTypes.REAL:
                                self._default = float(pp[1])
                            case StorageTypes.TEXT:
                                self._default = str(pp[1])
                            case StorageTypes.BLOB:
                                self._default = bytes(pp[1])
                        # end match
                    else:
                        # error! expect 'default <value>' - found extra spaces
                        pass

                    # need to verify the presence of the default value and matching values
                    if len(toks) > 0:
                        tok_default = fnmatch.filter(toks, 'default *')
                        self._valid &= len(tok_default) == 1
                        # if we're still valid one and exactly one was found
                        if self._valid:
                            # need to test if the default here and the one in the instance var match....
                            pass
                            # how to do this with the typing issue?
            # end if default

            # check if we
            if len(toks) > 0:
                self._valid &= propmap[p1] in toks
                toks.remove(propmap[p1])
        # for p in parts

        if self._default is None:
            self._sql_default = False
            match self._storageT:
                case StorageTypes.INTEGER:
                    self._default = 0
                case StorageTypes.REAL:
                    self._default = 0.0
                case StorageTypes.TEXT:
                    self._default = ''
                case StorageTypes.BLOB:
                    self._default = b''
            # end match _ct
        else:
            self.sql_default = True

        # now catch anything in the db not in the ini configuration - hopefully this is a no-op
        for t in toks:
            pass

    # end __init__

    def Validate(self, value: typing.Any) -> bool:
        """
        Checks if the value passed in is appropriate for this column.
        :param value: The candidate to validate.
        :return: True if the value can be used for this column, False otherwise.
        """
        return self._validator(value)

    def Set_Validator(self, vdator: type(len)):
        """
        Changes the validation function for a column.
        :param vdator: The new validator function.
        """
        self._validator = vdator

    def Build_Validator(self, vdator: str):
        """
        Changes the validator for the column based on a lambda expression from the vdator.
        :param vdator: A string describing the new validator.
        """
        tech, func = vdator.split(':')
        if tech.strip(' ').lower() == 'regex':
            self._validator = lambda x: re.search(func.strip(), x) != None
        elif tech.strip(' ').lower() == 'math':
            func[0] = 'x'
            self._validator = lambda x: func.strip(' ')

    # TODO replace this with getattr
    def ReadAttribute(self, attr: str) -> typing.Any:
        """
        Future proofing in case something shows up later we need easy access to.
        :param attr: The meta-data attribute to get.
        :return: The value of the attribute.
        """
        return self.pragma[self.headers.index(attr)]

    def Build_SQL(self) -> str:
        """
        Creates the SQL statement which creates this column.
        :return: The SQL statement for the column represented by this object.
        """
        # build the base string from the values in the system
        clause = f'{self.Name} {self.ColumnType}'

        # now check the optional fields
        if not self._isDefaultDefault():
            if self.ColumnType == 'text':
                clause = f'{clause} Default "{self.Default}"'
            else:
                clause = f'{clause} Default {self.Default}'
        if self.PrimaryKey > 0:
            clause = f'{clause} Primary Key'
        if not self.Nullable and not self.PrimaryKey:  # pk's are inherently not null
            clause = f'{clause} Not Null'

        # return the SQL
        return clause

    def _isDefaultDefault(self) -> bool:
        """
        Tests for a default value other than the sqlite standard.  If the default is the standard, no default
        clause is needed on the sql statement.
        :return:
        """
        # TODO figure out how to set this up as a CLASS variable
        defaults = {
            'integer': 0,
            'real': 0.0,
            'text': '',
            'null': None,
            'blob': b''
        }
        return self.Default == defaults[self.ColumnType]

    def make_sql(self, wname: bool = False) -> str:
        """
        Generates the part of the sql statement which creates this particular column.
        """
        # wname = with name, false means don't include the name of the column

        # add or don't the column name based on params
        if wname:
            sql = f"{self.name} {self._rawType}"
        else:
            sql = f"{self._rawType}"

        if not self.nullable and not self.pkey:
            sql = f"{sql} not null"
        if self.unique:
            sql = f"{sql} unique"
        if self._sql_default:
            if self.ctype == 'text':
                sql = f"{sql} default '{self.default}'"
            else:
                sql = f"{sql} default {self.default}"
        if self.fkey is not None:
            tnc = self.fkey.split('.')
            if len(tnc) != 2:
                # error for invalid foreign key format
                pass
            sql = f"{sql} foreign key({self.name}) references {tnc[0]}({tnc[1]})"
        if self.pkey:
            sql = f"{sql} primary key"

        return sql
    # make_sql

# end Class Column