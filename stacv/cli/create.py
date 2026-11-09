import os

from stacv.create import create_error
from stacv.create import rmii_template
from stacv.create import spi_template
from stacv.create import template

SPI_OPTIONS = ['wires', 'mode', 'spi_type', 'clock_period', 'sck_period']
REQUIRED_SPI_OPTIONS = ['wires', 'mode', 'spi_type']
DEFAULT_CLOCK_PERIOD = 10.0
DEFAULT_SCK_PERIOD = 40.0


def execute(oCmdLine):
    if oCmdLine.file_type == 'spi':
        return create_spi_files(oCmdLine)
    check_no_spi_options(oCmdLine)
    if oCmdLine.file_type == 'rmii':
        # RMII fixes its clock and edges, so the files need no options.
        write_files(find_output_directory(oCmdLine), rmii_template.create_files())
        return 0
    sTemplate = template.read_template(oCmdLine.file_type)
    if oCmdLine.output is None:
        print(sTemplate, end='')
    else:
        write_file(oCmdLine.output, sTemplate)
    return 0


def check_no_spi_options(oCmdLine):
    for sOption in SPI_OPTIONS:
        if getattr(oCmdLine, sOption) is not None:
            raise create_error.CreateError('create_002', f'--{format_option(sOption)} is an option of the spi template, not of the {oCmdLine.file_type} template')


def format_option(sOption):
    # The role is read into spi_type, as type names a Python builtin.
    if sOption == 'spi_type':
        return 'type'
    return sOption.replace('_', '-')


def create_spi_files(oCmdLine):
    for sOption in REQUIRED_SPI_OPTIONS:
        if getattr(oCmdLine, sOption) is None:
            raise create_error.CreateError('create_003', f'the spi template needs --{format_option(sOption)}')
    fClockPeriod = DEFAULT_CLOCK_PERIOD
    if oCmdLine.clock_period is not None:
        fClockPeriod = oCmdLine.clock_period
    fSckPeriod = DEFAULT_SCK_PERIOD
    if oCmdLine.sck_period is not None:
        fSckPeriod = oCmdLine.sck_period
    oOptions = spi_template.SpiOptions(oCmdLine.wires, oCmdLine.mode, oCmdLine.spi_type, fClockPeriod, fSckPeriod)
    dFiles = spi_template.create_files(oOptions)
    write_files(find_output_directory(oCmdLine), dFiles)
    return 0


def find_output_directory(oCmdLine):
    if oCmdLine.output is None:
        return '.'
    return oCmdLine.output


def write_files(sDirectory, dFiles):
    # Every file is checked before any is written, so a directory is never left half filled.
    for sName in dFiles:
        check_file_does_not_exist(os.path.join(sDirectory, sName))
    os.makedirs(sDirectory, exist_ok=True)
    for sName, lLines in dFiles.items():
        write_file(os.path.join(sDirectory, sName), '\n'.join(lLines) + '\n')


def check_file_does_not_exist(sFilename):
    # A filled-in file cannot be regenerated, so it is never overwritten.
    if os.path.exists(sFilename):
        raise create_error.CreateError('create_001', f'{sFilename} already exists; the template is not written')


def write_file(sFilename, sTemplate):
    check_file_does_not_exist(sFilename)
    print(f'Creating template {sFilename}')
    with open(sFilename, 'w') as oFile:
        oFile.write(sTemplate)
