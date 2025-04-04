import sqlite3
import typing

from Tables import Table
from Errors import *
from Definitions import *

class JoinedTable (Table):
    """
    A joined table is a left (primary) and right (secondary) table where the left table is extended with the columns
    from the right table based on common values in specific columns.  In classic DB speak this is a left join with
    the all the entries from the primary table present but only the matching entries from the secondary table.  The
    write commands ....

    When performing actions which might change the data it will only allow for changes to the primary table as multiple
    entries might map to the secondary from the primary (ie - the primary is people and the secondary are addresses, two
    people might share one).
    """

    # TODO how to handle the sql representation?  since this is all virtual return an empty string?

    @property
    def TableName(self):
        return f'{self._leftTable}/{self._rightTable}'


    def __init__(self, primary: Table, secondary: Table, primaryCol: str, secondaryCol: str):
        self._leftTable = primary.TableName
        self._rightTable = secondary.TableName
        self._leftcol = primaryCol
        self._rightcol = secondaryCol

        # grab the client
        self._client = primary._client

        # init the columns dictionary and primary keys list
        self._columns = {}  # this will hold _Column objects indexed by name
        self._pks = []  # a list of the names of primary keys
        self._filters = []  # where clauses

        for table in [primary, secondary]:
            # grab all the columns in the table
            for col in table._columns:

                # TODO add option to override this
                # if this is the one of the join keys skip it, keep things clean
                if f"{table.TableName}.{col}" == f"{self._leftTable}.{self._leftcol}":
                    continue
                if f"{table.TableName}.{col}" == f"{self._rightTable}.{self._rightcol}":
                    continue

                # copy the column into our set
                self._columns[f"{table.TableName}.{col}"] = table._columns[col]

                if table._columns[col].PrimaryKey:
                    self._pks.append(f"{table.TableName}.{col}")
            # end for col
        # end for table
    # end __init__()

    # region Hooks
    # These functions are available for inheriting classes to override, to change the behavior across multiple calls
    # within the API.
    def _hook_CheckColumn(self, col: str):
        if col not in self._columns.keys():
            raise ImaginaryColumn(self.TableName, col)

    def _hook_ValidateColumn(self, name: str, value: typing.Any):
        if not self._columns[name].Validate(value):
            raise InvalidColumnValue(self.TableName, name, value)

    def _hook_ApplyFilters(self, query: str, params: list) -> (str, list):
        # no filters, no work to do
        if len(self._filters):
            # Go ahead and add the first filter outside the loop, so we only need to
            # do the check for existing where statement once - this is a possible
            # performance improvement (not big, but still....)

            # check for a where clause already in the statement
            # not applicable now, but one day there might be an use case for function(s) with inline and
            # also the class filters
            if query.lower().find('where') > 0:
                # add an and to bridge the clauses
                query += ' and '
            else:
                # ok, this is the start of the where clause
                query += ' Where '

            # attach the first filter - outside loop because no and is needed
            # query += f'{self._buildWhere(self._filters[0].column, self._filters[0].operator, self._filters[0].value)}'
            query += f'{self._filters[0].column} {self._filters[0].operator.AsStr()} ?'
            params.append(self._filters[0].value)

            # add additional clauses if needed
            if len(self._filters) > 1:
                for f in self._filters[1:]:
                    # now append the actual clause
                    # query += f' and {self._buildWhere(f.column, f.operator, f.value)}'
                    query += f' and {f.column} {f.operator.AsStr()} ?'
                    params.append(f.value)
                # end for filters
            # end if len > 1
        # end if len

        return query, params

    def _hook_InLineFilter(self, query: str, params: list, name: str, operator: ComparisonOps, value: typing.Any) -> \
    (str, list):
        # raises an error if the column name is invalid
        self._hook_CheckColumn(name)

        # TODO verify the operation is valid for the column type => _hook_VerifyOp

        # raises an error if the value is invalid for the column
        self._hook_ValidateColumn(name, value)

        # add the where clause
        query += f' Where {name} {operator.AsStr()} ?'
        params.append(value)

        return query, params

    def _hook_BuildBaseQuery(self, operation: str, columns: list = []):
        if operation.lower() == 'select':
            # Select A.Cols, B.Cols from A left join B on A.ndx = B.a [where ....]
            return f"Select {str.join(', ', columns)} From {self._leftTable} Left Join {self._rightTable} on {self._leftTable}.{self._leftcol} = {self._rightTable}.{self._rightcol} "

        elif operation.lower() == 'insert':
            # insert into A (<cols>) values (?,?...); insert into B (<right_col>, <other cols> values (<left_col>, <other_vals>)
            if len(columns) == 1:
                return f"Insert into {self._leftTable}({columns[0]}) values (?)"
            elif len(columns) == 0:
                raise Exception()  # TODO replace with custom error for empty column list
            else:
                return f"Insert into {self._leftTable}({str.join(',', columns)}) values ({str.join(', ', ['?' for c in columns])})"
        # end if insert

        elif operation.lower() == 'delete':
            return f"Delete from {self._leftTable}"

        elif operation.lower() == 'update':
            if len(columns) == 1:
                return f"Update {self._leftTable} set {columns[0] + ' = ?'}"
            elif len(columns) == 0:
                raise Exception()  # TODO replace with custom error for empty column list
            else:
                return f"Update {self._leftTable} set {str.join(', ', [x + ' = ?' for x in columns])}"
        else:
            raise Exception()  # TODO replace with custom error for invalid db operation

    # endregion

    # region Helpers

    def _normalizeColumn(self, name: str) -> str:
        if name in self._columns.keys():
            return name
        elif f'{self._leftTable}.{name}' in self._columns.keys():
            return f'{self._leftTable}.{name}'
        else:
            raise ImaginaryColumn(self.TableName, name)

    # end _normalizeColumn

    # endregion

    # region Old Junk
    # def GetAll(self) -> list:
    #     """
    #     Performs a get for all the columns in the table.  Any filters set still apply to the results.
    #     :return: The results.
    #     """
    #     #TODO add flag for include primary keys or not - default false
    #     return self.Get(list(self._columns.keys()))
    #
    # def Get(self, columns: list) -> list:
    #     """
    #     Retrieves all values of a set of columns.  If the where clause is specified then only the matching values are
    #     returned.
    #
    #     :param columns: A list of the column names to select.  Every needs to be in the form TableName.ColumnName.
    #     :return:
    #     """
    #     #TODO if there is no tablename in the column entry then test if it's in the primary????
    #
    #     # sanity check the columns
    #     for c in columns:
    #         if c not in self._columns.keys():
    #             raise ImaginaryColumn(self.TableName, c)
    #     # end for c
    #
    #     # build the query - start with the basic select portion
    #     # initialize the select statement with the left join
    #     query = f"Select {str.join(', ', columns)} From {self.TableName}"
    #     query += f" Left Join {self._rightTable}"
    #     query += f" on {self.TableName}.{self._leftcol} = {self._rightTable}.{self._rightcol}"
    #
    #     # add the where clause(s)
    #     if len(self._filters) > 0:
    #         # add the intial where
    #         query += f" Where {self._buildWhere(self._filters[0].column, self._filters[0].operator, self._filters[0].value)}"
    #
    #         # add additional clauses if needed
    #         if len(self._filters) > 1:
    #             for f in self._filters:
    #                 query += f' and {self._buildWhere(f.column, f.operator, f.value)}'
    #             # end for filters
    #         # end if len > 1
    #     # end if len > 0
    #
    #     # execute the query
    #     print(query)
    #     cur = self._client.execute(query)
    #
    #     # marshall the results and return the rows
    #     return cur.fetchall()
    # endregion
