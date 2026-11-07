import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sExampleDir = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404')


def read_example_file(sFilename):
    with open(os.path.join(sExampleDir, sFilename)) as oFile:
        return oFile.read()


def replace_text(sText, lChanges):
    # Each change must match once, so a change to the example cannot leave a test checking nothing.
    if lChanges is None:
        return sText
    for sOld, sNew in lChanges:
        if sText.count(sOld) != 1:
            raise ValueError(f'{sOld!r} is in the example {sText.count(sOld)} times')
        sText = sText.replace(sOld, sNew)
    return sText


class InterfaceStandardTestCase(unittest.TestCase):
    '''
    The DAC81404 example, linked by the signals of SPI mode 1, with one change at a time.
    '''

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.addCleanup(self.oTempDir.cleanup)

    def write_files(self, lInterfaceChanges=None, lPartChanges=None, lTracesChanges=None):
        self.write_file('interface.toml', replace_text(read_example_file('interface.toml'), lInterfaceChanges))
        self.write_file('part.toml', replace_text(read_example_file('part.toml'), lPartChanges))
        self.write_file('traces.toml', replace_text(read_example_file('traces.toml'), lTracesChanges))

    def write_file(self, sFilename, sText):
        with open(os.path.join(self.oTempDir.name, sFilename), 'w') as oFile:
            oFile.write(sText)

    def run_block_diagram(self, lInterfaceChanges=None, lPartChanges=None, lTracesChanges=None):
        self.write_files(lInterfaceChanges, lPartChanges, lTracesChanges)
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        with mock.patch('sys.argv', ['stacv', 'visualize', 'block_diagram', sInterfaceFile]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def assert_error(self, sIdentifier, sFilename, sMessage, lInterfaceChanges=None, lPartChanges=None, lTracesChanges=None):
        self.assertEqual(2, self.run_block_diagram(lInterfaceChanges, lPartChanges, lTracesChanges))
        sPath = os.path.join(self.oTempDir.name, sFilename)
        self.assertEqual(f'ERROR: [{sIdentifier}] {sPath} {sMessage}\n', self.oStderr.getvalue())


class TestLinking(InterfaceStandardTestCase):

    def test_traces_are_linked_by_their_signals(self):
        self.assertEqual(0, self.run_block_diagram())
        lLines = self.oStdout.getvalue().split('\n')
        self.assertIn('  O_DAC_DATA   [X] --- data_output --> [X] SDIN', lLines)
        self.assertIn('  O_DAC_SDEN_F [X] --- chip_select --> [X] CSF', lLines)
        self.assertIn('  I_DAC_DATA   [X] <-- data_input ---- [X] SDO', lLines)
        self.assertIn('  O_DAC_SCLK   [X] --- clock --------> [X] SCLK', lLines)

    def test_a_repeated_signal_is_numbered(self):
        lInterfaceChanges = [('if_signal = "CS"', 'if_signal = "CS.1"')]
        lPartChanges = [('if_signal = "CS"', 'if_signal = "CS.1"')]
        lTracesChanges = [('if_signal = "CS"', 'if_signal = "CS.1"')]
        self.assertEqual(0, self.run_block_diagram(lInterfaceChanges, lPartChanges, lTracesChanges))

    def test_a_file_without_a_standard_links_by_pin_names(self):
        # The traces of the fixed example name their pins, as an interface that follows no standard does.
        with open(os.path.join(sProjectDir, 'tests', 'fixtures', 'dac81404', 'traces.toml')) as oFile:
            sTraces = oFile.read()
        lInterfaceChanges = [('if_standard = "SPI mode 1"\nif_role = "controller"\n', '')]
        lInterfaceChanges.extend([('idle = "low"\nif_signal = "SCK"\ngenerator = {source = "q_spi_output_clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_100mhz"}\n\n[[clock]]\nname = "dac_sclk_rd"', 'idle = "low"\ngenerator = {source = "q_spi_output_clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_100mhz"}\n\n[[clock]]\nname = "dac_sclk_rd"')])
        lInterfaceChanges.extend([('idle = "low"\nif_signal = "SCK"\n', 'idle = "low"\n'), ('if_signal = "COPI"\n', ''), ('if_signal = "CS"\n', ''), ('if_signal = "CIPO"\n', '')])
        self.write_files(lInterfaceChanges)
        self.write_file('traces.toml', sTraces)
        sInterfaceFile = os.path.join(self.oTempDir.name, 'interface.toml')
        with mock.patch('sys.argv', ['stacv', 'visualize', 'block_diagram', sInterfaceFile]):
            with contextlib.redirect_stdout(io.StringIO()):
                with contextlib.redirect_stderr(io.StringIO()) as oStderr:
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        self.assertEqual('', oStderr.getvalue())
        self.assertEqual(0, oContext.exception.code)


class TestStandardErrors(InterfaceStandardTestCase):

    def test_a_signal_without_a_standard_is_an_error(self):
        self.assert_error('if_standard_001', 'interface.toml', 'clock dac_sclk gives if_signal SCK, but the interface file names no if_standard', lInterfaceChanges=[('if_standard = "SPI mode 1"\n', '')])

    def test_an_unknown_standard_is_an_error(self):
        self.assert_error('if_standard_002', 'interface.toml', 'key "if_standard" names SPI mode 5; the standards are SPI mode 0, SPI mode 1, SPI mode 2 or SPI mode 3', lInterfaceChanges=[('if_standard = "SPI mode 1"', 'if_standard = "SPI mode 5"')])

    def test_a_standard_without_a_role_is_an_error(self):
        self.assert_error('if_standard_003', 'interface.toml', 'the interface file names if_standard SPI mode 1 but no if_role; give if_role controller or peripheral', lInterfaceChanges=[('if_role = "controller"\n', '')])

    def test_an_unknown_role_is_an_error(self):
        self.assert_error('if_standard_003', 'interface.toml', 'key "if_role" names master; the roles of SPI mode 1 are controller or peripheral', lInterfaceChanges=[('if_role = "controller"', 'if_role = "master"')])

    def test_an_unknown_signal_is_an_error(self):
        self.assert_error('if_standard_004', 'interface.toml', 'port O_DAC_DATA gives if_signal MOSI, which is not a signal of SPI mode 1; the signals are SCK, COPI, CIPO or CS', lInterfaceChanges=[('if_signal = "COPI"', 'if_signal = "MOSI"')])

    def test_a_signal_that_does_not_repeat_is_not_numbered(self):
        self.assert_error('if_standard_004', 'interface.toml', 'port O_DAC_DATA gives if_signal COPI.1, but COPI does not repeat, so it is not numbered', lInterfaceChanges=[('if_signal = "COPI"', 'if_signal = "COPI.1"')])

    def test_two_ports_with_one_signal_is_an_error(self):
        self.assert_error('if_standard_005', 'interface.toml', 'port O_DAC_DATA and port I_DAC_DATA both give if_signal COPI; a signal is carried by one port, or by clocks of one port', lInterfaceChanges=[('if_signal = "CIPO"', 'if_signal = "COPI"')])

    def test_two_part_pins_with_one_signal_is_an_error(self):
        self.assert_error('if_standard_005', 'part.toml', 'pin SDO of part interface Serial Interface gives if_signal COPI, which another pin of the interface gives; a signal is carried by one pin', lPartChanges=[('if_signal = "CIPO"', 'if_signal = "COPI"')])

    def test_a_part_interface_of_another_standard_is_an_error(self):
        self.assert_error('if_standard_006', 'part.toml', 'part interface Serial Interface follows SPI mode 0, but the interface file follows SPI mode 1', lPartChanges=[('if_standard = "SPI mode 1"', 'if_standard = "SPI mode 0"')])

    def test_a_part_in_the_device_role_is_an_error(self):
        self.assert_error('if_standard_006', 'part.toml', 'part interface Serial Interface is the controller, as is the device; the part must be the peripheral', lPartChanges=[('if_role = "peripheral"', 'if_role = "controller"')])

    def test_a_trace_signal_no_port_carries_is_an_error(self):
        lTracesChanges = [('if_signal = "CS"', 'if_signal = "CS.1"')]
        self.assert_error('if_standard_007', 'interface.toml', 'has no port or clock with if_signal CS.1, which trace chip_select carries', lTracesChanges=lTracesChanges)

    def test_a_trace_signal_no_part_pin_carries_is_an_error(self):
        lPartChanges = [('if_signal = "CS"', 'if_signal = "CS.2"')]
        self.assert_error('if_standard_008', 'part.toml', 'part interface Serial Interface has no pin with if_signal CS, which trace chip_select carries', lPartChanges=lPartChanges)

    def test_a_signal_without_a_trace_is_an_error(self):
        lTracesChanges = [('[[trace]]\nname = "data_input"\nif_signal = "CIPO"\npart_to_device = {}\n', '')]
        self.assert_error('if_standard_009', 'traces.toml', 'the traces file has no trace with if_signal CIPO, a signal of SPI mode 1', lTracesChanges=lTracesChanges)

    def test_a_trace_against_its_signal_is_an_error(self):
        lTracesChanges = [('if_signal = "COPI"\ndevice_to_part', 'if_signal = "COPI"\npart_to_device')]
        self.assert_error('if_standard_010', 'traces.toml', 'trace data_output carries COPI, which the controller drives, and the device is the controller, so the trace gives device_to_part and not part_to_device', lTracesChanges=lTracesChanges)

    def test_a_port_against_its_signal_is_an_error(self):
        lInterfaceChanges = [('if_signal = "COPI"', 'if_signal = "CIPO.X"'), ('if_signal = "CIPO"', 'if_signal = "COPI"'), ('if_signal = "CIPO.X"', 'if_signal = "CIPO"')]
        self.assert_error('if_standard_011', 'interface.toml', 'port O_DAC_DATA carries CIPO, which the peripheral drives, and the device is the controller, so the port is an input; methodology SDR-SS-O times an output', lInterfaceChanges=lInterfaceChanges)

    def test_a_part_pin_against_its_signal_is_an_error(self):
        lPartChanges = [('if_signal = "COPI"', 'if_signal = "CIPO.X"'), ('if_signal = "CIPO"', 'if_signal = "COPI"'), ('if_signal = "CIPO.X"', 'if_signal = "CIPO"')]
        self.assert_error('if_standard_011', 'part.toml', 'pin SDIN of part interface Serial Interface carries CIPO, which the peripheral drives, and the part is the peripheral, so the pin is an output; methodology SDR-SS-I is not', lPartChanges=lPartChanges)

    def test_a_clock_that_idles_at_the_other_level_is_an_error(self):
        lInterfaceChanges = [('if_standard = "SPI mode 1"', 'if_standard = "SPI mode 3"')]
        lPartChanges = [('if_standard = "SPI mode 1"', 'if_standard = "SPI mode 3"')]
        self.assert_error('if_standard_012', 'interface.toml', 'clock dac_sclk idles low, but the clock of SPI mode 3 idles high', lInterfaceChanges=lInterfaceChanges, lPartChanges=lPartChanges)

    def test_port_edges_of_another_mode_are_an_error(self):
        # Mode 0 samples on the rising edge; O_DAC_DATA is captured on falling edges D and B.
        lInterfaceChanges = [('if_standard = "SPI mode 1"', 'if_standard = "SPI mode 0"')]
        lPartChanges = [('if_standard = "SPI mode 1"', 'if_standard = "SPI mode 0"')]
        self.assert_error('if_standard_012', 'interface.toml', 'port O_DAC_DATA uses falling edges of dac_sclk, but SPI mode 0 samples data on rising edges', lInterfaceChanges=lInterfaceChanges, lPartChanges=lPartChanges)

    def test_part_pin_edges_of_another_mode_are_an_error(self):
        lPartChanges = [('if_signal = "COPI"\nclock = {pin = "SCLK", max_frequency = 25}\ncapture_edge = "Falling"', 'if_signal = "COPI"\nclock = {pin = "SCLK", max_frequency = 25}\ncapture_edge = "Rising"')]
        self.assert_error('if_standard_012', 'part.toml', 'pin SDIN of part interface Serial Interface captures on the rising edge, but SPI mode 1 samples data on the falling edge', lPartChanges=lPartChanges)


class TestReaderErrors(InterfaceStandardTestCase):

    def test_a_trace_with_a_signal_and_a_pin_is_an_error(self):
        lTracesChanges = [('if_signal = "COPI"', 'if_signal = "COPI"\ndevice_pin = "O_DAC_DATA"')]
        self.assert_error('traces_config_011', 'traces.toml', 'trace data_output gives if_signal and a pin; give if_signal, or device_pin and part_pin', lTracesChanges=lTracesChanges)

    def test_a_clock_pin_has_only_a_name_and_a_signal(self):
        lPartChanges = [('name = "SCLK"\nif_signal = "SCK"', 'name = "SCLK"\nif_signal = "SCK"\ncapture_edge = "Rising"')]
        self.assert_error('part_config_004', 'part.toml', 'key "capture_edge" in pin SCLK of interface Serial Interface is not a key stacv reads; the keys are name, if_signal', lPartChanges=lPartChanges)
