import contextlib
import io
import os
import re
import tempfile
import unittest
from unittest import mock

from stacv import __main__

sProjectDir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sDacDir = os.path.join(sProjectDir, 'example', 'texas_instruments', 'DAC81404')
# Each example interface file, and the eye stacv visualize eye draws for it beside it.
lExamples = []
for sInterface in ['mdio', 'mii', 'rmii', 'rgmii', 'rgmii_id']:
    lExamples.append(f'example/microchip/vsc8540et/{sInterface}')
lExamples.append('example/texas_instruments/DAC81404/interface')
lExamples.append('example/analog_devices/ad7399/if_dac_spi')


class EyeTestCase(unittest.TestCase):

    def setUp(self):
        sWorkingDir = os.getcwd()
        self.addCleanup(os.chdir, sWorkingDir)
        os.chdir(sProjectDir)
        oEnvironment = mock.patch.dict(os.environ, {'PROJ_DIR': sProjectDir})
        oEnvironment.start()
        self.addCleanup(oEnvironment.stop)

    def run_eye(self, sInterfaceFile):
        self.oStdout = io.StringIO()
        self.oStderr = io.StringIO()
        with mock.patch('sys.argv', ['stacv', 'visualize', 'eye', sInterfaceFile]):
            with contextlib.redirect_stdout(self.oStdout):
                with contextlib.redirect_stderr(self.oStderr):
                    with self.assertRaises(SystemExit) as oContext:
                        __main__.main()
        return oContext.exception.code


class TestExampleEyes(EyeTestCase):
    '''
    The eye of every example interface is the one in the example, drawn from the example's timing reports.
    '''

    def test_every_example_eye_matches(self):
        for sExample in lExamples:
            with self.subTest(interface=sExample):
                iExitCode = self.run_eye(f'{sExample}.toml')
                with open(f'{sExample}_eye.txt') as oFile:
                    sExpected = oFile.read()
                self.assertEqual('', self.oStderr.getvalue())
                self.assertEqual(0, iExitCode)
                self.assertEqual(sExpected, self.oStdout.getvalue())


class TestEyeDrawing(EyeTestCase):
    '''
    The DAC81404's O_DAC_DATA: setup 10 ns, hold 10 ns, and a 16 ns window.
    '''

    def draw_with_setup_slack(self, sSlack):
        # Every setup report of the example's O_DAC_DATA gets the same slack.
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        sReport = os.path.join(oTemporaryDirectory.name, 'O_DAC_DATA_timing.rpt')
        with open(os.path.join(sProjectDir, 'tests', 'fixtures', 'dac81404', 'timing_reports', 'O_DAC_DATA_timing.rpt')) as oFile:
            sText = oFile.read()
        sText = re.sub(r'Slack \(MET\) :\s+(\S+)ns(\s+\(required time - arrival time\)\n  Source:[^\n]*\n[^\n]*\n  Destination:[^\n]*\n[^\n]*\n  Path Group:[^\n]*\n  Path Type:\s+Max)', f'Slack (VIOLATED) :        {sSlack}ns\\2', sText)
        sInterfaceFile = os.path.join(oTemporaryDirectory.name, 'interface.toml')
        with open(os.path.join(sDacDir, 'interface.toml')) as oFile:
            sInterface = oFile.read()
        sInterface = sInterface.replace('"part.toml"', f'"{os.path.join(sDacDir, "part.toml")}"').replace('"traces.toml"', f'"{os.path.join(sDacDir, "traces.toml")}"')
        sInterface = sInterface.replace('$PROJ_DIR/example/texas_instruments/DAC81404/timing_reports/O_DAC_DATA_timing.rpt', sReport)
        with open(sInterfaceFile, 'w') as oFile:
            oFile.write(sInterface)
        with open(sReport, 'w') as oFile:
            oFile.write(sText)
        self.assertEqual(0, self.run_eye(sInterfaceFile))
        return self.oStdout.getvalue().split('\n')

    def test_a_negative_setup_slack_puts_the_setup_time_past_the_eye(self):
        # The data settles 10 - 2 = 8 ns before the edge, so the setup arrow starts 2 ns into the change.
        lLines = self.draw_with_setup_slack('-2.000')
        lExpected = []
        lExpected.append('O_DAC_DATA (SDR-SS-O)')
        lExpected.append('  setup 10 ns, hold 10 ns, 1.17 ns a character')
        lExpected.append(' ' * 53 + 'setup slack  hold slack  offset from eye centre')
        lExpected.append('    Slow  XXXXXXX<--------|-------->......XXXXXXXXX    -2.000 ns    7.438 ns               -4.719 ns')
        lExpected.append('    Fast  XXXXXXX<--------|-------->......XXXXXXXXX    -2.000 ns    7.167 ns               -4.583 ns')
        lExpected.append('    All   XXXXXXX<--------|-------->......XXXXXXXXX    -2.000 ns    7.167 ns               -4.583 ns')
        self.assertEqual(lExpected, lLines[0:6])


class TestNoEye(EyeTestCase):

    def test_a_first_and_last_clock_port_has_no_eye(self):
        # Its setup and hold are against different edges, so there is no one window to centre.
        self.assertEqual(0, self.run_eye('example/texas_instruments/DAC81404/interface.toml'))
        self.assertIn('\nO_DAC_SDEN_F (SDR-SS-O-FLC): no eye, timed to the first and last clock edges\n\n', self.oStdout.getvalue())
