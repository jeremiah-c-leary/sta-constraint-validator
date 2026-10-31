import os
import re
import tempfile
import unittest
from types import SimpleNamespace

from stacv.traces import traces
from stacv.traces import traces_config_error


class TestDefaultDelay(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        self.sTracesFile = os.path.join(oTemporaryDirectory.name, 'traces.toml')

    def read_traces(self, lLines):
        with open(self.sTracesFile, 'w') as oFile:
            oFile.write('\n'.join(lLines) + '\n')
        return traces.create_trace_list(SimpleNamespace(traces=self.sTracesFile))

    def build_trace(self, sDelays):
        lLines = []
        lLines.append('[[trace]]')
        lLines.append('name = "chip_select"')
        lLines.append('device_pin = "O_DAC_CSF"')
        lLines.append('part_pin = "CSF"')
        lLines.append(f'device_to_part = {sDelays}')
        return lLines

    def build_error_pattern(self, sIdentifier, sMessage):
        return r'ERROR: \[' + sIdentifier + r'\] ' + re.escape(self.sTracesFile) + ' ' + re.escape(sMessage) + '$'

    def test_empty_delays_take_the_default_maximum_delay(self):
        lLines = ['default_delay = {max_delay = 1.0, min_delay = 0.0}'] + self.build_trace('{}')
        oTrace = self.read_traces(lLines).traces[0]
        self.assertEqual(1.0, oTrace.device_to_part.max_delay)

    def test_empty_delays_take_the_default_minimum_delay(self):
        lLines = ['default_delay = {max_delay = 1.0, min_delay = 0.0}'] + self.build_trace('{}')
        oTrace = self.read_traces(lLines).traces[0]
        self.assertEqual(0.0, oTrace.device_to_part.min_delay)

    def test_empty_delays_are_marked_as_default(self):
        lLines = ['default_delay = {max_delay = 1.0, min_delay = 0.0}'] + self.build_trace('{}')
        oTrace = self.read_traces(lLines).traces[0]
        self.assertTrue(oTrace.device_to_part.is_default)

    def test_written_delays_are_not_marked_as_default(self):
        lLines = ['default_delay = {max_delay = 1.0, min_delay = 0.0}'] + self.build_trace('{max_delay = 3.0, min_delay = 1.0}')
        oTrace = self.read_traces(lLines).traces[0]
        self.assertFalse(oTrace.device_to_part.is_default)

    def test_raises_error_if_empty_delays_have_no_default(self):
        sError = self.build_error_pattern('traces_config_001', 'trace chip_select has no delays in key "device_to_part" and no default_delay is defined')
        with self.assertRaisesRegex(traces_config_error.TracesConfigError, sError):
            self.read_traces(self.build_trace('{}'))

    def test_raises_error_if_only_one_delay_is_given(self):
        lLines = ['default_delay = {max_delay = 1.0, min_delay = 0.0}'] + self.build_trace('{max_delay = 3.0}')
        sError = self.build_error_pattern('traces_config_002', 'trace chip_select key "device_to_part" must give both max_delay and min_delay, or neither')
        with self.assertRaisesRegex(traces_config_error.TracesConfigError, sError):
            self.read_traces(lLines)
