'''
Formats rows of text into columns, with a header and a separator.
'''


def format_table(lRows, iColumnGap):
    lWidths = get_column_widths(lRows)
    lLines = []
    lLines.append(format_row(lRows[0], lWidths, iColumnGap))
    lLines.append(build_separator(lWidths, iColumnGap))
    for lRow in lRows[1:]:
        lLines.append(format_row(lRow, lWidths, iColumnGap))
    return lLines


def get_column_widths(lRows):
    lWidths = []
    for iColumn in range(len(lRows[0])):
        iMaxLength = 0
        for lRow in lRows:
            iMaxLength = max(iMaxLength, len(lRow[iColumn]))
        lWidths.append(iMaxLength)
    return lWidths


def format_row(lRow, lWidths, iColumnGap):
    sRow = ''
    for sColumn, iWidth in zip(lRow, lWidths):
        sRow += f'{sColumn:<{iWidth}}' + ' ' * iColumnGap
    sRow = sRow.rstrip()
    return sRow


def build_separator(lWidths, iColumnGap):
    sRow = ''
    for iWidth in lWidths:
        sRow += '-' * iWidth + ' ' * iColumnGap
    sRow = sRow.rstrip()
    return sRow
