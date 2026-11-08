'''
Where in an SPI configuration file a key is, with its line, for error messages.

TOML does not give the line a value came from, so the line is found by its table header and key in the text.
'''

import re

from stacv.config import config_location

TABLE_HEADER = re.compile(r'\s*\[\s*([A-Za-z0-9_-]+)\s*\]\s*(#.*)?')


class SpiConfigLocation(config_location.ConfigLocation):

    def __init__(self, sFilename, lLines):
        config_location.ConfigLocation.__init__(self, sFilename)
        self.lines = lLines

    def set_key(self, sTable, sKey):
        # A missing key is reported at its table's header, where it would be added.
        iLine = find_key_line(self.lines, sTable, sKey)
        if iLine is None and sTable is not None:
            iLine = find_table_line(self.lines, sTable)
        self.location = describe_location(sTable, iLine)

    def set_table(self, sTable):
        self.location = describe_location(sTable, find_table_line(self.lines, sTable))


def find_key_line(lLines, sTable, sKey):
    # Keys before the first table header are top-level keys, which have no table.
    sCurrentTable = None
    oKey = re.compile(rf'\s*{re.escape(sKey)}\s*=')
    for iLine, sLine in enumerate(lLines, start=1):
        oHeader = TABLE_HEADER.fullmatch(sLine)
        if oHeader is not None:
            sCurrentTable = oHeader.group(1)
        elif sCurrentTable == sTable and oKey.match(sLine) is not None:
            return iLine
    return None


def find_table_line(lLines, sTable):
    for iLine, sLine in enumerate(lLines, start=1):
        oHeader = TABLE_HEADER.fullmatch(sLine)
        if oHeader is not None and oHeader.group(1) == sTable:
            return iLine
    return None


def describe_location(sTable, iLine):
    sLocation = ''
    if sTable is not None:
        sLocation += f' in [{sTable}]'
    if iLine is not None:
        sLocation += f' (line {iLine})'
    return sLocation
