from tests.cli import test_traces_errors

build_trace = test_traces_errors.build_trace


class TestTracesValues(test_traces_errors.TracesTestCase):
    '''
    The values of the traces file, and the pins it names in the interface and part files.
    '''

    def test_trace_without_a_direction_is_an_error(self):
        self.assert_error([build_trace(sDelays=None)], 'traces_config_007', 'trace clock has neither device_to_part nor part_to_device')

    def test_maximum_delay_less_than_minimum_delay_is_an_error(self):
        sDelays = 'device_to_part = {max_delay = 1.0, min_delay = 3.0}'
        self.assert_error([build_trace(sDelays=sDelays)], 'traces_config_008', 'trace clock key "device_to_part" has max_delay 1.0 less than min_delay 3.0')

    def test_default_delay_maximum_less_than_minimum_is_an_error(self):
        lText = ['default_delay = {max_delay = 0.0, min_delay = 1.0}', build_trace(sDelays='device_to_part = {}')]
        self.assert_error(lText, 'traces_config_008', 'default_delay has max_delay 0.0 less than min_delay 1.0')

    def test_trace_defined_twice_is_an_error(self):
        self.assert_error([build_trace(), build_trace()], 'traces_config_009', 'trace clock is defined by more than one [[trace]] table')
