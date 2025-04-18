import sqlite3
import typing

from Columns import Column
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
        return f'{self._primaryT}/{self._secondT}'


    def __init__(self, primary: Table, secondary: Table, primaryCol: str, secondaryCol: str):
        self._primaryT = primary.TableName
        self._secondT = secondary.TableName
        self._primaryKey = primaryCol
        self._secondKey = secondaryCol

        # grab the client
        self._client = primary._client

        # init the columns dictionary and primary keys list
        self._columns = {}  # this will hold two lists of columns, one for the primary and the other for the secondary
        self._columns[primary.TableName] = []
        self._columns[secondary.TableName] = []
        self._pks = []  # a list of the names of primary keys
        self._filters = []  # where clauses

        for table in [primary, secondary]:
            # grab all the columns in the table
            for col in table._columns:

                # TODO add option to override this
                # if this is the one of the join keys skip it, keep things clean
                if f"{table.TableName}.{col}" == f"{self._primaryT}.{self._primaryKey}":
                    continue
                if f"{table.TableName}.{col}" == f"{self._secondT}.{self._secondKey}":
                    continue

                # copy the column into the correct list
                self._columns[table.TableName].append(col)

                if table._columns[col].PrimaryKey:
                    self._pks.append(f"{table.TableName}.{col}")
            # end for col
        # end for table
    # end __init__()

    # region Hooks
    # These functions are available for inheriting classes to override, to change the behavior across multiple calls
    # within the API.
    def _hook_CheckColumn(self, col: str) -> typing.Union[Column, None]:
        normed = None
        match col.count('.'):
            case 0:
                if col in self._columns[self._primaryT]:
                    normed = next(c for c in self._columns[self._primaryT] if c.Name == col)
                elif col in self._columns[self._secondT]:
                    normed = next(c for c in self._columns[self._primaryT] if c.Name == col)
            case 1:
                [t, c] = col.split('.')
                if t in self._columns.keys():
                    if c in self._columns[t]:
                        normed = next(cx for cx in self._columns[t] if cx.Name == c)
            # all other cases (the _ case) are invalid, and should return None
        return normed

    def _hook_ValidateColumn(self, col: Column, value: typing.Any) -> bool:
        return col.Validate(value)

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
        col = self._hook_CheckColumn(name)
        if col is None:
            raise ImaginaryColumn(self.TableName, name)

        # raises an error if the value is invalid for the column
        if not self._hook_ValidateColumn(col, value):
            raise InvalidColumnValue(self.TableName, col.Name, value)

        # add the where clause
        query += f' Where {self._normalizeColumn(col)} {operator.AsStr()} ?'
        params.append(value)

        return query, params

    def _hook_BuildBaseQuery(self, operation: str, columns: list[Column] = []):
        if operation.lower() == 'select':
            # Select A.Cols, B.Cols from A left join B on A.ndx = B.a [where ....]
            return f"Select {str.join(', ', columns)} From {self._primaryT} Left Join {self._secondT} on {self._primaryT}.{self._primaryKey} = {self._secondT}.{self._secondKey} "

        elif operation.lower() == 'insert':
            # insert into A (<cols>) values (?,?...); insert into B (<right_col>, <other cols> values (<left_col>, <other_vals>)
            if len(columns) == 1:
                return f"Insert into {self._primaryT}({columns[0]}) values (?)"
            elif len(columns) == 0:
                raise Exception()  # TODO replace with custom error for empty column list
            else:
                return f"Insert into {self._primaryT}({str.join(',', columns)}) values ({str.join(', ', ['?' for c in columns])})"
        # end if insert

        elif operation.lower() == 'delete':
            return f"Delete from {self._primaryT}"

        elif operation.lower() == 'update':
            """
            This needs some re-processing
            if the column being set is in the primary table, just run the set with the primaryT's key...what if filter on secondary?
            if the column is in the secondary then there will be a need to do teh 'join' via a seondary key = select key from primaryT....
            if there are filters, they will need to be applied either within the main query or the secondary select, based on which table they actually touch
            there is a lot more complexity here, maybe we need a query object to pass around so the whole thing, base query, filters, et all can be combined in one shot?
            """
            if len(columns) == 1:
                return f"Update {self._primaryT} set {columns[0] + ' = ?'}"
            elif len(columns) == 0:
                raise Exception()  # TODO replace with custom error for empty column list
            else:
                return f"Update {self._primaryT} set {str.join(', ', [x + ' = ?' for x in columns])}"
        else:
            raise Exception()  # TODO replace with custom error for invalid db operation

    # endregion

    def _normalizeColumn(self, col: Column) -> str:
        if col in self._columns[self._primaryT]:
            return f"{self._primaryT}.{col.Name}"
        elif col in self._columns[self._secondT]:
            return f"{self._secondT}.{col.Name}"
        else:
            raise ImaginaryColumn(self.TableName, col.Name)

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
