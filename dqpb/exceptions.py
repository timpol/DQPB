"""
Custom exceptions.

"""

class XlSelectionError(Exception):
    """
    Raised when there is an error selecting or reading data from
    spreadsheet.
    """
    pass


class ValidationError(Exception):
    """
    Raised when a user input or selection is invalid for the given task.
    """
    pass
