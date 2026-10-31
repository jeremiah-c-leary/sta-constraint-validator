'''
Builds a table of the md5sum and name of each input file.
'''

import hashlib


REPORT_WIDTH = 80
MD5SUM_COLUMN_WIDTH = 32
COLUMN_GAP = 2
MAXIMUM_FILENAME_COLUMN_WIDTH = REPORT_WIDTH - MD5SUM_COLUMN_WIDTH - COLUMN_GAP


def build_md5sum_table(lFiles):
    lLines = build_md5sum_table_header(lFiles)
    lLines.extend(build_md5sum_table_rows(lFiles))
    return lLines


def build_md5sum_table_header(lFiles):
    lLines = []
    sGap = ' '*COLUMN_GAP
    lLines.append(f'{"md5sum":<{MD5SUM_COLUMN_WIDTH}}{sGap}Filename')
    lLines.append(build_md5sum_separator(lFiles))
    return lLines


def build_md5sum_separator(lFiles):
    iFileColumnWidth = calculate_filename_column_width(lFiles)
    sLine = '-'*MD5SUM_COLUMN_WIDTH + ' '*COLUMN_GAP + '-'*iFileColumnWidth
    return sLine


def calculate_filename_column_width(lFiles):
    iFileColumnWidth = len('Filename')
    for sFile in lFiles:
        iFileColumnWidth = max(iFileColumnWidth, len(sFile))
    if total_width_exceeds_report_width(iFileColumnWidth):
        iFileColumnWidth = MAXIMUM_FILENAME_COLUMN_WIDTH
    return iFileColumnWidth


def total_width_exceeds_report_width(iFileColumnWidth):
    return iFileColumnWidth > MAXIMUM_FILENAME_COLUMN_WIDTH


def build_md5sum_table_rows(lFiles):
    lLines = []
    for sFile in lFiles:
        sMd5sum = generate_md5sum(sFile)
        lLines.append(sMd5sum + ' '*COLUMN_GAP + sFile)
    return lLines


def generate_md5sum(sFilename):
    with open(sFilename, 'rb') as oFile:
        return hashlib.file_digest(oFile, 'md5').hexdigest()
