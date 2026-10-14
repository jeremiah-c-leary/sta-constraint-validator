'''
Classes that check the schema of values passed to them.
'''

class ArrayOfTablesType():
    def __init__(self):
        self.description = 'an array of tables'

    def is_valid(self, value):
        if not isinstance(value, list):
            return False
        for item in value:
            if not isinstance(item, dict):
                return False
        return True


class ListOfStringsType():

    def __init__(self):
        self.description = 'a list of strings'

    def is_valid(self, value):
        if not isinstance(value, list):
            return False
        for item in value:
            if not isinstance(item, str):
                return False
        return True


class StringType():

    def __init__(self):
        self.description = 'a string'

    def is_valid(self, value):
        return isinstance(value, str)


ARRAY_OF_TABLES = ArrayOfTablesType()
LIST_OF_STRINGS = ListOfStringsType()
STRING = StringType()
