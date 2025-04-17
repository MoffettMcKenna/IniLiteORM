import typing

import Columns
from Definitions import ComparisonOps


class ImaginaryColumn(BaseException):
    """
    Exception for when the user asks for a column which doesn't exist.
    """

    def __init__(self, table: str, col: str):
        """
        Constructor
        :param table:  Name of the table the column didn't exist in.
        :param col:  Name of the non-existent column.
        """
        self.Table = table
        self.Column = col

    def __str__(self):
        return f'Tried to read non-existent column {self.Column} from {self.Table}.'


class InvalidColumnValue(BaseException):
    """
    Exception for when a column's validate function fails.
    """

    def __init__(self, table: str, col: str, val: typing.Any):
        """
        Constructor
        :param table:  The name of the table containing the column.
        :param col:  The column the data was meant to go in.
        :param val:  The data value which failed to validate for the column.
        """
        self.Table = table
        self.ColumnName = col
        self.Value = val

    def __str__(self):
        return f'Validate function failed for {self.Table}.{self.ColumnName} with value "{self.Value}"'

class InvalidOperation(BaseException):
    """
    Triggers when an operation is attempted on a column with a datatype that doesn't support it.
    """

    def __init__(self, table: str, col: Columns.Column, op: ComparisonOps):
        """
        Constructor
        :param table: The name of the table the column is in.
        :param col: THe column the inappropriate operation was attempted with.
        :param op: The operator attempted.
        """
        self.Table = table
        self.ColumnName = col.Name
        self.DataType = col.ColumnType
        self.Operation = op

    def __str__(self):
        return f'Cannot do a {self.Operation.AsStr()} on a column of type {self.DataType} on {self.Table}.{self.ColumnName}'
