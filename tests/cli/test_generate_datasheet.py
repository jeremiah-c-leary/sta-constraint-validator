import contextlib
import io
import os
import tempfile
import tomllib
import unittest
from unittest import mock

from stacv import __main__
from stacv.generate import datasheet_drawing
from stacv.part import part

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sFixtureDir = os.path.join(sProjectDir, 'tests', 'fixtures', 'dac81404')
sFixtureReportDir = os.path.join(sFixtureDir, 'timing_reports')


def build_fixture_interface_text():
    # The DAC81404 example with the edges and timing reports of the fixed reports: I_DAC_DATA captured on Y and I.
    with open(os.path.join(sFixtureDir, 'interface.toml')) as oFile:
        sText = oFile.read()
    sText = sText.replace('setup_edge = 28, hold_edge = 12', 'setup_edge = 24, hold_edge = 8')
    sText = sText.replace('$PROJ_DIR/example/texas_instruments/DAC81404/timing_reports', sFixtureReportDir)
    sText = sText.replace('part = "part.toml"', f'part = "{os.path.join(sFixtureDir, "part.toml")}"')
    sText = sText.replace('traces = "traces.toml"', f'traces = "{os.path.join(sFixtureDir, "traces.toml")}"')
    return sText


def build_second_output_port():
    lText = []
    lText.append('')
    lText.append('[[port]]')
    lText.append('status = "analyze"')
    lText.append('name = "O_DAC_DATA_2"')
    lText.append('methodology = "SDR-SS-O"')
    lText.append('launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}')
    lText.append('capture_clock = {name = "dac_sclk", setup_edge = 3, hold_edge = 1}')
    lText.append('registers = ["q_spi_output_data_reg"]')
    lText.append(f'timing_reports = ["{os.path.join(sFixtureReportDir, "O_DAC_DATA_timing.rpt")}"]')
    return '\n'.join(lText) + '\n'


class DatasheetTestCase(unittest.TestCase):

    def setUp(self):
        self.oTempDir = tempfile.TemporaryDirectory()
        self.addCleanup(self.oTempDir.cleanup)

    def write_interface(self, sText):
        sFilename = os.path.join(self.oTempDir.name, 'interface.toml')
        with open(sFilename, 'w') as oFile:
            oFile.write(sText)
        return sFilename

    def run_datasheet(self, sInterfaceFile):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'generate', 'datasheet', sInterfaceFile]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code

    def get_output_lines(self):
        return self.oStdout.getvalue().split('\n')

    def get_section(self, sTitle):
        # The lines from the section heading to the next heading.
        lLines = self.get_output_lines()
        iStart = lLines.index(sTitle) + 2
        iEnd = iStart
        while iEnd < len(lLines) and not lLines[iEnd].startswith('====') and lLines[iEnd] != "'''":
            iEnd += 1
        return lLines[iStart:iEnd]

    def get_pin_tables(self):
        dDatasheet = tomllib.loads(self.oStdout.getvalue())
        return dDatasheet['pin']


class TestDatasheetValues(DatasheetTestCase):
    '''
    The values of each methodology, from the fixed DAC81404 timing reports, the worst of the Slow and Fast corners.
    '''

    def setUp(self):
        DatasheetTestCase.setUp(self)
        self.assertEqual(0, self.run_datasheet(self.write_interface(build_fixture_interface_text())))

    def test_timing_table_gives_each_value(self):
        # O_DAC_DATA:   tCOmax = 20 - 7.260 - 12 = 0.740, tCOmin = -20 + 7.167 + 12 = -0.833
        # O_DAC_SDEN_F: tB = 9.228 + 30 = 39.228, tA = 6.195 + 13 = 19.195
        # I_DAC_DATA:   tSU = 20 - (34 + 0.219), tH = (1 - 42.667) + 40 + 40 - 20
        lExpected = []
        lExpected.append('')
        lExpected.append('  Pin           Parameter   Value   Unit')
        lExpected.append('  ------------  ---------  -------  ----')
        lExpected.append('  O_DAC_DATA    tCOmin      -0.833  ns')
        lExpected.append('                tCOmax       0.740  ns')
        lExpected.append('  ------------  ---------  -------  ----')
        lExpected.append('  O_DAC_SDEN_F  tB          39.228  ns')
        lExpected.append('                tA          19.195  ns')
        lExpected.append('  ------------  ---------  -------  ----')
        lExpected.append('  I_DAC_DATA    tSU          5.781  ns')
        lExpected.append('                tH          -1.667  ns')
        self.assertEqual(lExpected, self.get_section('2  Timing')[0:11])

    def test_round_trip_text_gives_the_capture_and_the_window(self):
        lLines = self.get_section('5  I_DAC_DATA')
        lExpected = []
        lExpected.append('The part launches the data on each rising edge of O_DAC_SCLK, and the device')
        lExpected.append('captures it with its own clock, 40 ns after that rising edge at its pins.  The')
        lExpected.append('device needs the data stable from 34.219 ns to 38.333 ns after the rising edge')
        lExpected.append('that launched it:')
        self.assertEqual(lExpected, lLines[1:5])

    def test_pin_tables_give_each_value_with_its_symbol_and_section(self):
        lPins = self.get_pin_tables()
        self.assertEqual({'value': 0.74, 'symbol': 'tCOmax', 'source': 'Section 3'}, lPins[0]['cko_max'])
        self.assertEqual({'value': -0.833, 'symbol': 'tCOmin', 'source': 'Section 3'}, lPins[0]['cko_min'])
        self.assertEqual('Rising', lPins[0]['launch_edge'])
        self.assertEqual({'value': 39.228, 'symbol': 'tB', 'source': 'Section 4'}, lPins[1]['valid_before'])
        self.assertEqual({'value': 19.195, 'symbol': 'tA', 'source': 'Section 4'}, lPins[1]['valid_after'])
        self.assertEqual('Falling', lPins[1]['launch_edge'])
        self.assertEqual({'value': 5.781, 'symbol': 'tSU', 'source': 'Section 5'}, lPins[2]['setup'])
        self.assertEqual({'value': -1.667, 'symbol': 'tH', 'source': 'Section 5'}, lPins[2]['hold'])
        self.assertEqual('Falling', lPins[2]['capture_edge'])

    def test_pin_tables_give_the_clock_port_and_frequency(self):
        lPins = self.get_pin_tables()
        self.assertEqual({'pin': 'O_DAC_SCLK', 'max_frequency': 25}, lPins[0]['clock'])
        self.assertEqual({'pin': 'O_DAC_SCLK', 'max_frequency': 12.5}, lPins[2]['clock'])

    def test_pin_tables_can_be_read_as_part_file_pins(self):
        # A design that connects to the device copies the pin tables into its part file.
        dPart = {}
        dPart['properties'] = {'manufacturer': 'AMD', 'part_number': 'dac81404_spi'}
        dPart['datasheet'] = {'name': 'DAC_SPI_1 Interface Datasheet', 'url': 'datasheet.toml', 'version': '1'}
        dPart['interface'] = [{'name': 'DAC_SPI_1', 'pin': self.get_pin_tables()}]
        oPart = part.build_part(dPart, 'part.toml')
        self.assertEqual(-0.833, oPart.get_pin_named('O_DAC_DATA').cko_min.value)
        self.assertEqual(39.228, oPart.get_pin_named('O_DAC_SDEN_F').valid_before.value)
        self.assertEqual(5.781, oPart.get_pin_named('I_DAC_DATA').setup.value)

    def test_notes_name_the_clock_and_the_corners(self):
        lLines = self.get_section('2  Timing')
        lExpected = []
        lExpected.append("Every time is at the device's pins, against the edge of O_DAC_SCLK at its pin.")
        lExpected.append('Each value is the worst of the Slow and Fast process corners.')
        lExpected.append('The rising and falling edges of O_DAC_SCLK are assumed to leave the device')
        lExpected.append('with the same delay.')
        self.assertEqual(lExpected, lLines[12:16])


class TestRepeatedSymbols(DatasheetTestCase):
    '''
    A symbol more than one port gives is numbered in the order of the ports, and a port's symbols share its number.
    '''

    def test_two_ports_of_one_methodology_number_their_symbols(self):
        self.assertEqual(0, self.run_datasheet(self.write_interface(build_fixture_interface_text() + build_second_output_port())))
        lLines = self.get_section('2  Timing')
        self.assertEqual('  O_DAC_DATA    tCOmin_1    -0.833  ns', lLines[3])
        self.assertEqual('                tCOmax_1     0.740  ns', lLines[4])
        self.assertEqual('  I_DAC_DATA    tSU          5.781  ns', lLines[9])
        self.assertEqual('  O_DAC_DATA_2  tCOmin_2    -0.833  ns', lLines[12])
        self.assertEqual('                tCOmax_2     0.740  ns', lLines[13])
        lPins = self.get_pin_tables()
        self.assertEqual('tCOmax_2', lPins[3]['cko_max']['symbol'])
        self.assertEqual('Section 6', lPins[3]['cko_max']['source'])


class TestPortsLeftOut(DatasheetTestCase):
    '''
    Every port of the interface is accounted for: a port without a section is listed with the reason.
    '''

    def test_a_deferred_port_is_listed(self):
        sText = build_fixture_interface_text().replace('status = "analyze"\nname = "O_DAC_SDEN_F"', 'status = "defer"\nname = "O_DAC_SDEN_F"')
        self.assertEqual(0, self.run_datasheet(self.write_interface(sText)))
        lLines = self.get_section('2  Timing')
        self.assertIn('These ports are not in this datasheet:', lLines)
        self.assertIn('  O_DAC_SDEN_F  deferred', lLines)
        lNames = []
        for dPin in self.get_pin_tables():
            lNames.append(dPin['name'])
        self.assertEqual(['O_DAC_DATA', 'I_DAC_DATA'], lNames)

    def test_a_methodology_without_a_datasheet_is_listed(self):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(sProjectDir)
        with mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir}):
            self.assertEqual(0, self.run_datasheet('example/microchip/vsc8540et/mii.toml'))
        lLines = self.get_section('2  Timing')
        self.assertEqual('No port of the interface is in this datasheet.', lLines[1])
        self.assertIn('  O_MII_TX_EN     SDR-SS-RT-DO, which stacv cannot write a datasheet for yet', lLines)
        self.assertIn('  I_MII_RX_DV     SDR-SS-I, which stacv cannot write a datasheet for yet', lLines)


class TestDatasheetErrors(DatasheetTestCase):

    def test_launch_off_the_forwarded_clock_edges_is_an_error(self):
        # Edge 7 is at 35 ns, between the edges of dac_sclk at 20 and 40 ns.
        sText = build_fixture_interface_text().replace('setup_edge = 8, hold_edge = 8}\ncapture_clock = {name = "dac_sclk", setup_edge = 3', 'setup_edge = 7, hold_edge = 7}\ncapture_clock = {name = "dac_sclk", setup_edge = 3')
        self.assertEqual(2, self.run_datasheet(self.write_interface(sText)))
        self.assertEqual('ERROR: [generate_011] port O_DAC_DATA launch edge 7 at 35 ns is not at an edge of dac_sclk; the datasheet gives the clock to out from the clock edge the data is launched with\n', self.oStderr.getvalue())


class TestDrawing(unittest.TestCase):
    '''
    The edge and each value are drawn in time order, so a value is on the side of the edge its sign puts it.
    '''

    def test_values_either_side_of_the_edge_share_an_arrow_row(self):
        lMarkers = [datasheet_drawing.Marker('tCOmin', -0.908), datasheet_drawing.Marker('tCOmax', 0.689)]
        oDrawing = datasheet_drawing.Drawing('O_DAC_SCLK', 'Rising', 'O_DAC_DATA', lMarkers, ['_', '#', '_'])
        lExpected = []
        lExpected.append('                                   ____________________')
        lExpected.append('  O_DAC_SCLK  ____________________/')
        lExpected.append('')
        lExpected.append('                   |<-- tCOmin -->|<-- tCOmax -->|')
        lExpected.append('              _____ _____________________________ _____')
        lExpected.append('  O_DAC_DATA  _____X#############################X_____')
        self.assertEqual(lExpected, datasheet_drawing.draw(oDrawing))

    def test_values_on_one_side_of_the_edge_have_an_arrow_row_each(self):
        # Both after the edge: the longer arrow is drawn above the shorter.
        lMarkers = [datasheet_drawing.Marker('tCOmin', 0.5), datasheet_drawing.Marker('tCOmax', 2.0)]
        oDrawing = datasheet_drawing.Drawing('SCLK', 'Falling', 'DATA', lMarkers, ['_', '#', '_'])
        lExpected = []
        lExpected.append('        _____')
        lExpected.append('  SCLK       \\___________________________________')
        lExpected.append('')
        lExpected.append('             |<--------- tCOmax ---------->|')
        lExpected.append('             |<-- tCOmin -->|')
        lExpected.append('        ____________________ ______________ _____')
        lExpected.append('  DATA  ____________________X##############X_____')
        self.assertEqual(lExpected, datasheet_drawing.draw(oDrawing))

    def test_a_value_at_the_edge_has_no_arrow(self):
        lMarkers = [datasheet_drawing.Marker('tB', 0.0)]
        oDrawing = datasheet_drawing.Drawing('SCLK', 'Falling', 'CS', lMarkers, ['#', '_'])
        lExpected = []
        lExpected.append('        _____')
        lExpected.append('  SCLK       \\_____')
        lExpected.append('')
        lExpected.append('        _____ _____')
        lExpected.append('  CS    #####X_____')
        self.assertEqual(lExpected, datasheet_drawing.draw(oDrawing))
