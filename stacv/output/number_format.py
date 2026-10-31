'''
Formats numbers for the text stacv writes.
'''


def format_number(fNumber):
    # Up to three decimals, without trailing zeros.
    return f'{fNumber:.3f}'.rstrip('0').rstrip('.')
