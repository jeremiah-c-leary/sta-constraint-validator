'''
Classes that check the schema of values passed to them.
'''

class ArrayOfTablesType():

    def __init__(self):
        self.description = 'an array of one or more tables'

    def is_valid(self, value):
        if not isinstance(value, list):
            return False
        if len(value) == 0:
            return False
        for item in value:
            if not isinstance(item, dict):
                return False
        return True


class ListOfStringsType():

    def __init__(self):
        self.description = 'a list of one or more strings'

    def is_valid(self, value):
        if not isinstance(value, list):
            return False
        if len(value) == 0:
            return False
        for item in value:
            if not isinstance(item, str):
                return False
        return True


class StringType():

    def __init__(self):
        self.description = 'a non-empty string'

    def is_valid(self, value):
        if not isinstance(value, str):
            return False
        if len(value) == 0:
            return False
        return True


class NumberType():

    def __init__(self):
        self.description = 'a number'

    def is_valid(self, value):
        # A TOML true or false is a bool, which Python also counts as an int.
        if isinstance(value, bool):
            return False
        return isinstance(value, (int, float))


class TableType():

    def __init__(self):
        self.description = 'a table'

    def is_valid(self, value):
        return isinstance(value, dict)


ARRAY_OF_TABLES = ArrayOfTablesType()
LIST_OF_STRINGS = ListOfStringsType()
STRING = StringType()
NUMBER = NumberType()
TABLE = TableType()
