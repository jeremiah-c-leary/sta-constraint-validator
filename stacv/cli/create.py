import os

from stacv.create import create_error
from stacv.create import template


def execute(oCmdLine):
    sTemplate = template.read_template(oCmdLine.file_type)
    if oCmdLine.output is None:
        print(sTemplate, end='')
    else:
        write_file(oCmdLine.output, sTemplate)
    return 0


def write_file(sFilename, sTemplate):
    # A filled-in file cannot be regenerated, so it is never overwritten.
    if os.path.exists(sFilename):
        raise create_error.CreateError('create_001', f'{sFilename} already exists; the template is not written')
    print(f'Creating template {sFilename}')
    with open(sFilename, 'w') as oFile:
        oFile.write(sTemplate)
