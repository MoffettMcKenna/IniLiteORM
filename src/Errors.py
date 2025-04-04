

class ImaginaryColumn(BaseException):
    """
    Exception for when the user asks for a column which doesn't exist.
    """

    def __init__(self, table, col):
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

    def __int__(self, table, col, val):
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

