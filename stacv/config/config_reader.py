'''
Reads the keys of an input file, and raises the errors that every input file shares.
'''

import tomllib

from stacv.config import value_type


class ConfigReader():

    def __init__(self, sFamily, cError):
        # The family names the errors, such as interface_config, and cError is the error class of the file.
        self.family = sFamily
        self.error = cError

    def raise_error(self, iNumber, sFilename, sMessage):
        raise self.error(f'{self.family}_{iNumber:03d}', sFilename, sMessage)

    def read_toml_file(self, sFilename):
        with open(sFilename, 'rb') as oFile:
            try:
                return tomllib.load(oFile)
            except tomllib.TOMLDecodeError as oError:
                self.raise_error(1, sFilename, f'is not valid TOML: {oError}')

    def get_required_key_value(self, dDict, sKey, oLocation):
        if sKey not in dDict:
            self.raise_error(2, oLocation.filename, f'missing required key "{sKey}"{oLocation.location}')
        return dDict[sKey]

    def get_required_string(self, dDict, sKey, oLocation):
        return self.get_required_value_of_type(dDict, sKey, value_type.STRING, oLocation)

    def get_required_list_of_strings(self, dDict, sKey, oLocation):
        return self.get_required_value_of_type(dDict, sKey, value_type.LIST_OF_STRINGS, oLocation)

    def get_required_number(self, dDict, sKey, oLocation):
        return self.get_required_value_of_type(dDict, sKey, value_type.NUMBER, oLocation)

    def get_required_table(self, dDict, sKey, oLocation):
        return self.get_required_value_of_type(dDict, sKey, value_type.TABLE, oLocation)

    def get_required_array_of_tables(self, dDict, sKey, oLocation):
        return self.get_required_value_of_type(dDict, sKey, value_type.ARRAY_OF_TABLES, oLocation)

    def get_required_value_of_type(self, dDict, sKey, oExpectedType, oLocation):
        value = self.get_required_key_value(dDict, sKey, oLocation)
        self.check_schema(oExpectedType, value, sKey, oLocation)
        return value

    def check_schema(self, oExpectedType, value, sKey, oLocation):
        if not oExpectedType.is_valid(value):
            self.raise_error(3, oLocation.filename, f'key "{sKey}"{oLocation.location} must be {oExpectedType.description}')

    def check_keys(self, dDict, lKeys, oLocation):
        # A misspelled key would otherwise be ignored, so every key must be one stacv reads.
        for sKey in dDict:
            if sKey not in lKeys:
                self.raise_error(4, oLocation.filename, f'key "{sKey}"{oLocation.location} is not a key stacv reads; the keys are {", ".join(lKeys)}')
