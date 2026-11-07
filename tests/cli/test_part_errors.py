import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

SDR_SS_I_KEYS = 'name, methodology, if_signal, clock, capture_edge, setup, hold'

INTERFACE_TEXT = '''description = "part errors test"
name = "DAC_SPI_1"
part = "part.toml"
part_interface = "SPI"
traces = "traces.toml"

[[port]]
status = "defer"
name = "O_DATA"
'''

TRACES_TEXT = '''[[trace]]
name = "data_output"
device_pin = "O_DATA"
part_pin = "DATA_IN"
device_to_part = {max_delay = 3.0, min_delay = 1.0}
'''

PROPERTIES = '''[properties]
manufacturer = "MANUFACTURER"
part_number = "PART_NUMBER"'''

DATASHEET = '''[datasheet]
name = "DATASHEET_NAME"
url = "DATASHEET_URL"
version = "DATASHEET_VERSION"'''

INTERFACE = '''[[interface]]
name = "SPI"'''


def build_pin(lReplacements=(), sName='DATA_IN'):
    # Each replacement is (key, line): the line replaces the key's line, or removes it when None.
    dLines = {}
    dLines['name'] = f'name = "{sName}"'
    dLines['methodology'] = 'methodology = "SDR-SS-I"'
    dLines['clock'] = 'clock = {pin = "CLK", max_frequency = 25}'
    dLines['capture_edge'] = 'capture_edge = "Falling"'
    dLines['setup'] = 'setup = {value = 10, symbol = "tSetup", source = "Table X"}'
    dLines['hold'] = 'hold = {value = 10, symbol = "tHold", source = "Table X"}'
    for sKey, sLine in lReplacements:
        dLines[sKey] = sLine
    lText = ['[[interface.pin]]']
    for sLine in dLines.values():
        if sLine is not None:
            lText.append(sLine)
    return '\n'.join(lText)


class PartTestCase(unittest.TestCase):
    '''
    The part file is read through stacv visualize block_diagram, after a valid traces file.
    '''

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sDirectory = oTemporaryDirectory.name
        self.sPartFile = os.path.join(self.sDirectory, 'part.toml')
        self.write_file('interface.toml', INTERFACE_TEXT)
        self.write_file('traces.toml', TRACES_TEXT)

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.sDirectory, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_block_diagram(self, lPartText):
        self.write_file('part.toml', '\n\n'.join(lPartText) + '\n')
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        lArgv = ['stacv', 'visualize', 'block_diagram', os.path.join(self.sDirectory, 'interface.toml')]
        with mock.patch('sys.argv', lArgv):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_error(self, lPartText, sIdentifier, sMessage):
        iExitCode = self.run_block_diagram(lPartText)
        self.assertEqual(f'ERROR: [{sIdentifier}] {self.sPartFile} {sMessage}\n', self.oStderr.getvalue())
        self.assertEqual('', self.oStdout.getvalue())
        self.assertEqual(2, iExitCode)


class TestPartErrors(PartTestCase):

    def test_invalid_toml_is_an_error(self):
        iExitCode = self.run_block_diagram(['[properties'])
        self.assertTrue(self.oStderr.getvalue().startswith(f'ERROR: [part_config_001] {self.sPartFile} is not valid TOML: '))
        self.assertEqual(2, iExitCode)

    def test_part_without_a_datasheet_is_an_error(self):
        self.assert_error([PROPERTIES, INTERFACE, build_pin()], 'part_config_002', 'missing required key "datasheet"')

    def test_properties_without_a_part_number_is_an_error(self):
        self.assert_error(['[properties]\nmanufacturer = "MANUFACTURER"', DATASHEET, INTERFACE, build_pin()], 'part_config_002', 'missing required key "part_number" in [properties]')

    def test_pin_without_a_clock_is_an_error(self):
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin([('clock', None)])], 'part_config_002', 'missing required key "clock" in pin DATA_IN of interface SPI')

    def test_pin_without_a_name_is_named_by_its_number(self):
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(), build_pin([('name', None)])], 'part_config_002', 'missing required key "name" in pin number 2 of interface SPI')

    def test_setup_without_a_symbol_is_an_error(self):
        sSetup = 'setup = {value = 10, source = "Table X"}'
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin([('setup', sSetup)])], 'part_config_002', 'missing required key "symbol" in setup of pin DATA_IN of interface SPI')

    def test_properties_must_be_a_table(self):
        self.assert_error(['properties = "PART_NUMBER"', DATASHEET, INTERFACE, build_pin()], 'part_config_003', 'key "properties" must be a table')

    def test_max_frequency_must_be_a_number(self):
        sClock = 'clock = {pin = "CLK", max_frequency = "25"}'
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin([('clock', sClock)])], 'part_config_003', 'key "max_frequency" in clock of pin DATA_IN of interface SPI must be a number')

    def test_unknown_top_level_key_is_an_error(self):
        sDatasheet = DATASHEET.replace('[datasheet]', '[datsheet]')
        self.assert_error([PROPERTIES, sDatasheet, INTERFACE, build_pin()], 'part_config_004', 'key "datsheet" is not a key stacv reads; the keys are properties, datasheet, interface')

    def test_misspelled_pin_key_is_an_error(self):
        lReplacements = [('capture_edge', 'capture_egde = "Falling"')]
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(lReplacements)], 'part_config_004', f'key "capture_egde" in pin DATA_IN of interface SPI is not a key stacv reads; the keys are {SDR_SS_I_KEYS}')

    def test_key_of_another_methodology_is_an_error(self):
        lReplacements = [('launch_edge', 'launch_edge = "Rising"')]
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(lReplacements)], 'part_config_004', f'key "launch_edge" in pin DATA_IN of interface SPI is not a key stacv reads; the keys are {SDR_SS_I_KEYS}')

    def test_unknown_pin_methodology_is_an_error(self):
        lReplacements = [('methodology', 'methodology = "SDR-SS-X"')]
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(lReplacements)], 'part_config_005', 'key "methodology" in pin DATA_IN of interface SPI names SDR-SS-X; a part pin is SDR-SS-I, SDR-SS-O, SDR-SS-O-FLC, SDR-SS-RT-DI, SDR-SS-RT-DO, SDR-SYS-I, SDR-SYS-O, DDR-SS-I or DDR-SS-O')

    def test_valid_part_file_draws_the_block_diagram(self):
        iExitCode = self.run_block_diagram([PROPERTIES, DATASHEET, INTERFACE, build_pin()])
        self.assertEqual('', self.oStderr.getvalue())
        self.assertEqual(0, iExitCode)
