from tests.cli import test_interface_keys

build_interface = test_interface_keys.build_interface


class TestInterfaceValues(test_interface_keys.InterfaceTestCase):
    '''
    The values of the interface keys: edges in the notation of their role, periods, and duplicate ports.
    '''

    def test_launch_edge_written_as_a_letter_is_an_error(self):
        sLaunchClock = 'launch_clock = {name = "clk_launch", setup_edge = "I", hold_edge = 8}'
        self.assert_error({'launch_clock': sLaunchClock}, 'interface_config_014', 'key "launch_clock" in port O_DATA has setup_edge "I"; launch edges are numbers: 0, 1, 2, ...')

    def test_negative_launch_edge_is_an_error(self):
        sLaunchClock = 'launch_clock = {name = "clk_launch", setup_edge = 8, hold_edge = -2}'
        self.assert_error({'launch_clock': sLaunchClock}, 'interface_config_014', 'key "launch_clock" in port O_DATA has hold_edge -2; launch edges are numbers: 0, 1, 2, ...')

    def test_capture_edge_written_as_a_letter_is_an_error(self):
        sCaptureClock = 'capture_clock = {name = "clk_capture", setup_edge = "D", hold_edge = 1}'
        self.assert_error({'capture_clock': sCaptureClock}, 'interface_config_015', 'key "capture_clock" in port O_DATA has setup_edge "D"; capture edges are numbers: 0, 1, 2, ...')

    def test_negative_capture_edge_is_an_error(self):
        sCaptureClock = 'capture_clock = {name = "clk_capture", setup_edge = 3, hold_edge = -1}'
        self.assert_error({'capture_clock': sCaptureClock}, 'interface_config_015', 'key "capture_clock" in port O_DATA has hold_edge -1; capture edges are numbers: 0, 1, 2, ...')

    def test_capture_edge_past_nine_is_accepted(self):
        sCaptureClock = 'capture_clock = {name = "clk_capture", setup_edge = 27, hold_edge = 25}'
        iExitCode = self.run_edges(build_interface({'capture_clock': sCaptureClock}))
        self.assertNotIn('interface_config_015', self.oStderr.getvalue() + self.oStdout.getvalue())

    def test_zero_period_is_an_error(self):
        self.assert_error({'clock_1': '[[clock]]\nname = "clk_launch"\nperiod = 0'}, 'interface_config_016', 'key "period" of clock clk_launch must be greater than 0')

    def test_negative_period_is_an_error(self):
        self.assert_error({'clock_1': '[[clock]]\nname = "clk_launch"\nperiod = -10.0'}, 'interface_config_016', 'key "period" of clock clk_launch must be greater than 0')

    def test_port_with_the_same_name_and_methodology_twice_is_an_error(self):
        sSecondPort = build_interface().split('[[port]]')[1]
        self.assert_error({'timing_reports': 'timing_reports = ["O_DATA_timing.rpt"]\n[[port]]' + sSecondPort.rstrip('\n')}, 'interface_config_017', 'port O_DATA with methodology SDR-SS-O is defined by more than one [[port]] table')
