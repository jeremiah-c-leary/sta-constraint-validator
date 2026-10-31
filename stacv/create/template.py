'''
Reads the templates of the interface, traces and part files.
'''

import os

FILE_TYPES = ['interface', 'traces', 'part']
TEMPLATE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'templates')


def read_template(sFileType):
    with open(os.path.join(TEMPLATE_DIRECTORY, f'{sFileType}.toml')) as oFile:
        return oFile.read()
