'''
Contains functions to assist with formatting the details of rule results.
'''


def format_detail(oLine, sMessage):
    return f'{oLine.filename}:{oLine.line_number}  {sMessage}'
