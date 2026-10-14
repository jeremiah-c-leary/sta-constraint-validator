
class StringType():

    def __init__(self):
        self.description = 'a string'

    def is_valid(self, value):
        return isinstance(value, str)


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


STRING = StringType()
LIST_OF_STRINGS = ListOfStringsType()
