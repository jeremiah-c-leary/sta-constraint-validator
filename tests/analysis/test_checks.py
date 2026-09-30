import copy
import os
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET

from stacv import utils
from stacv.analysis import checks, registry
from stacv.output import junit

sRoot = os.path.join(os.path.dirname(__file__), '..', '..')
sReportDir = os.path.join(sRoot, 'tests', 'timing_report', 'parse', 'vivado')
lReports = [os.path.join(sReportDir, s) for s in ('dac_spi.setup.rpt', 'dac_spi.hold.rpt')]
dConfig = utils.read_config_file(os.path.join(sRoot, 'tests', 'analysis', 'config_edge6.yaml'))


def run(dConfigOverride=None, corners=('Slow', 'Fast')):
    return checks.validate(dConfigOverride or dConfig, checks.load_reports(lReports), corners)


def pin(lValidations, sPin):
    return next(v for v in lValidations if v.pin == sPin)


def statuses(oValidation):
    return {r.check_id: r.status for r in oValidation.results}


class TestRegistry(unittest.TestCase):

    def test_ids_are_unique_and_well_formed(self):
        lIds = [c.check_id for c in registry.CHECKS]
        self.assertEqual(len(lIds), len(set(lIds)))
        for sId in lIds:
            self.assertRegex(sId, r'^(INT|COV|STR|EDG|DLY|SLK)-\d{3}$')

    def test_dependencies_exist(self):
        for oCheck in registry.CHECKS:
            for sDep in oCheck.requires:
                self.assertIn(sDep, registry.BY_ID)

    def test_run_order_respects_dependencies(self):
        lSeen = set()
        for oCheck in checks.run_order():
            self.assertTrue(set(oCheck.requires) <= lSeen, oCheck.check_id)
            lSeen.add(oCheck.check_id)

    def test_every_check_has_a_runner(self):
        self.assertEqual(set(registry.BY_ID), set(checks.runners(dConfig, ('Fast',))))

    def test_documentation_lists_every_check(self):
        sRst = registry.to_rst()
        for oCheck in registry.CHECKS:
            self.assertIn(f'{oCheck.check_id}: {oCheck.title}', sRst)


class TestExample(unittest.TestCase):

    def setUp(self):
        self.data = pin(run(), 'O_DAC_DATA')

    def test_all_pins_listed(self):
        self.assertEqual(['O_DAC_DATA', 'O_DAC_CSF', 'O_DAC_DATA_BUS[4]', 'I_DAC_DATA'], [v.pin for v in run()])

    def test_results_in_registry_order(self):
        self.assertEqual([c.check_id for c in registry.CHECKS], [r.check_id for r in self.data.results])

    def test_stages(self):
        self.assertEqual({
            'INT-001': 'pass', 'INT-002': 'pass', 'INT-003': 'fail',
            'COV-001': 'pass', 'COV-002': 'fail',
            'STR-001': 'pass', 'STR-002': 'pass', 'STR-003': 'pass', 'STR-004': 'pass', 'STR-005': 'pass',
            'EDG-001': 'fail', 'EDG-002': 'fail',
            'DLY-001': 'fail', 'DLY-002': 'fail',
            'SLK-001': 'skip', 'SLK-002': 'skip',
        }, statuses(self.data))

    def test_intent_disagreement_names_the_edge(self):
        self.assertIn('captures SDIN on the falling edge', self.data.result('INT-003').message)

    def test_bus_hold_edge_disagreement(self):
        oBus = pin(run(), 'O_DAC_DATA_BUS[4]')
        self.assertEqual('fail', oBus.result('INT-003').status)
        self.assertIn('hold uses the falling edge', oBus.result('INT-003').message)

    def test_crpr_matches_vivado(self):
        self.assertIn('expected 0.245 ns, report removes 0.245 ns', self.data.result('STR-005').details[0])

    def test_derived_output_delays(self):
        self.assertIn('expected 6.500 ns', self.data.result('DLY-001').message)
        self.assertIn('expected -5.500 ns', self.data.result('DLY-002').message)

    def test_skip_names_blocking_ids(self):
        self.assertEqual('Not checked until these pass: COV-002, EDG-001, DLY-001.',
                         self.data.result('SLK-001').message)

    def test_missing_reports_block_later_stages(self):
        oCsf = pin(run(), 'O_DAC_CSF')
        self.assertEqual('fail', oCsf.result('COV-001').status)
        self.assertEqual('pass', oCsf.result('INT-003').status)
        self.assertEqual(12, oCsf.count(checks.SKIP))


class TestStructureFailures(unittest.TestCase):

    def test_wrong_capture_clock_pin(self):
        dChanged = copy.deepcopy(dConfig)
        dInterface = dChanged['device']['interface'][0]['DAC_DATA']
        dInterface['clock']['output'].append({'O_OTHER_CLK': {'frequency': '20 MHz'}})
        dInterface['data']['output'][0]['O_DAC_DATA']['capture_clock']['name'] = 'O_OTHER_CLK'
        dChanged['board']['trace'].append({'other': {'device_pin': 'O_OTHER_CLK', 'part_pin': 'SCLK',
                                                     'delay': {'max': 1.0, 'min': 0.5}}})
        oData = pin(run(dChanged), 'O_DAC_DATA')
        self.assertEqual('fail', oData.result('STR-002').status)
        self.assertEqual('skip', oData.result('STR-004').status)

    def test_missing_trace_blocks_coverage(self):
        dChanged = copy.deepcopy(dConfig)
        dChanged['board']['trace'] = [t for t in dChanged['board']['trace'] if 'data_out' not in t]
        oData = pin(run(dChanged), 'O_DAC_DATA')
        self.assertEqual('fail', oData.result('INT-001').status)
        self.assertEqual('skip', oData.result('COV-001').status)


class TestCorrectedConstraints(unittest.TestCase):
    '''Intent adjusted to what the reports do on the setup side.'''

    def test_setup_side_passes_hold_stays_flagged(self):
        dFixed = copy.deepcopy(dConfig)
        dPin = dFixed['device']['interface'][0]['DAC_DATA']['data']['output'][0]['O_DAC_DATA']
        dPin['launch_clock']['edge'] = 9
        dPin['capture_clock']['edge'] = {'setup': 'c', 'hold': 'a'}
        dPart = dFixed['part']['interface'][0]['serial_data']['data']['input'][0]['SDIN']
        dPart['rising'] = dPart.pop('falling')
        dPart['rising']['setup']['value'] = 0.5     # 0.5 + 2.5 - 1.0 = 2.0
        dPart['rising']['hold']['value'] = -0.5     # 0.5 + 2.5 - 2.0 = 1.0
        dFixed['board']['trace'][1]['data_out']['delay']['min'] = 2.5
        oData = pin(run(dFixed, corners=('Fast',)), 'O_DAC_DATA')
        for sId in ('INT-003', 'COV-002', 'EDG-001', 'DLY-001', 'DLY-002', 'SLK-001'):
            self.assertEqual('pass', oData.result(sId).status, sId)
        # Vivado's default hold check compares the next launch edge with the
        # setup capture edge; no intended launch/capture pair reproduces it.
        self.assertEqual('fail', oData.result('EDG-002').status)
        self.assertEqual('skip', oData.result('SLK-002').status)


class TestJunit(unittest.TestCase):

    def test_counts_and_structure(self):
        oRoot = junit.build(run())
        self.assertEqual('64', oRoot.get('tests'))
        oSuite = oRoot.find("testsuite[@name='DAC_DATA.O_DAC_DATA']")
        self.assertEqual(6, len(oSuite.findall('testcase/failure')))
        self.assertEqual(2, len(oSuite.findall('testcase/skipped')))

    def test_testcase_named_by_id(self):
        oRoot = junit.build(run())
        oCase = oRoot.find("testsuite[@name='DAC_DATA.O_DAC_DATA']/testcase[@name='EDG-001']")
        self.assertIsNotNone(oCase)
        self.assertTrue(oCase.find('failure').get('message').startswith(registry.get('EDG-001').title))

    def test_written_file_parses(self):
        with tempfile.TemporaryDirectory() as sDir:
            sFile = os.path.join(sDir, 'results.xml')
            junit.write(run(), sFile)
            self.assertEqual('testsuites', ET.parse(sFile).getroot().tag)


class TestBothCornersReport(unittest.TestCase):
    '''Owner's report with slow and fast corners and wrapped clock edge rows.'''

    def setUp(self):
        self.paths = checks.load_reports([os.path.join(sReportDir, 'O_DAC_DATA_timing.rpt')])
        dEdge7 = utils.read_config_file(os.path.join(os.path.dirname(__file__), 'config_edge7.yaml'))
        self.data = pin(checks.validate(dEdge7, self.paths), 'O_DAC_DATA')

    @unittest.skip('rewriting parser to return objects.  Remove when completed.')
    def test_wrapped_edge_rows_parse(self):
        self.assertEqual([('hold', 'Slow'), ('setup', 'Slow'), ('hold', 'Fast'), ('setup', 'Fast')],
                         [(p.check, p.corner.split()[0]) for p in self.paths])
        oSlowSetup = self.paths[1]
        self.assertEqual((40.0, 50.0, 48.151, 55.638), (oSlowSetup.launch_edge, oSlowSetup.capture_edge,
                                                         oSlowSetup.arrival, oSlowSetup.required))

    def test_corners_now_covered(self):
        self.assertEqual('pass', self.data.result('COV-002').status)

    def test_crpr_within_rounding(self):
        self.assertEqual('pass', self.data.result('STR-005').status)

    def test_edge7_intent(self):
        self.assertIn('intended edge 7 to c (+20.000 ns)', self.data.result('EDG-001').message)
        self.assertIn('intended edge 7 to a (-30.000 ns)', self.data.result('EDG-002').message)
        self.assertNotIn('expected falling', self.data.result('EDG-001').message)


class TestMulticycleReport(unittest.TestCase):
    '''Owner's report with -setup 2 -start and -hold 2 -start multicycle paths.'''

    def setUp(self):
        dEdge7 = utils.read_config_file(os.path.join(os.path.dirname(__file__), 'config_edge7.yaml'))
        oPaths = checks.load_reports([os.path.join(sReportDir, 'O_DAC_DATA_timing_mcp_hold2.rpt')])
        self.data = pin(checks.validate(dEdge7, oPaths), 'O_DAC_DATA')

    def test_setup_edges_match(self):
        self.assertEqual('pass', self.data.result('EDG-001').status)

    def test_hold_edges_reported_literally_and_from_launch(self):
        sMessage = self.data.result('EDG-002').message
        self.assertIn('report checks edge 3 to a (-10.000 ns), intended edge 7 to a (-30.000 ns)', sMessage)
        self.assertIn('from edge 7, where the data changes, this captures at 20.000 ns', sMessage)

    def test_anchored_hold(self):
        oAnchored = self.data.comparisons[0].anchored('hold')
        self.assertEqual((30.0, 20.0), (oAnchored.launch_time, oAnchored.capture_time))
        self.assertEqual('edge 7', oAnchored.launch_label)
        self.assertEqual('20.000 ns (no edge)', oAnchored.capture_label)


class TestMulticycleHold4Report(unittest.TestCase):
    '''Same design with -hold 4 -start: both edge checks match the intent.'''

    def setUp(self):
        dEdge7 = utils.read_config_file(os.path.join(os.path.dirname(__file__), 'config_edge7.yaml'))
        oPaths = checks.load_reports([os.path.join(sReportDir, 'O_DAC_DATA_timing_mcp_hold4.rpt')])
        self.data = pin(checks.validate(dEdge7, oPaths), 'O_DAC_DATA')

    def test_both_edge_checks_pass(self):
        self.assertEqual('pass', self.data.result('EDG-001').status)
        self.assertEqual('pass', self.data.result('EDG-002').status)

    def test_anchored_hold_reaches_a(self):
        oAnchored = self.data.comparisons[0].anchored('hold')
        self.assertEqual((30.0, 0.0, 'a'), (oAnchored.launch_time, oAnchored.capture_time,
                                            oAnchored.capture_label))

    def test_only_delays_and_intent_remain(self):
        lFailed = [r.check_id for r in self.data.results if r.status == checks.FAIL]
        self.assertEqual(['INT-003', 'DLY-001', 'DLY-002'], lFailed)


class TestEdge11Intent(unittest.TestCase):
    '''Owner's config with launch edge 11, setup c, hold d, against the hold 4 report.'''

    def setUp(self):
        dEdge11 = utils.read_config_file(os.path.join(os.path.dirname(__file__), 'config_edge11.yaml'))
        oPaths = checks.load_reports([os.path.join(sReportDir, 'O_DAC_DATA_timing_mcp_hold4.rpt')])
        self.data = pin(checks.validate(dEdge11, oPaths), 'O_DAC_DATA')

    def test_report_edges_keep_report_labels(self):
        sMessage = self.data.result('EDG-002').message
        self.assertIn('report checks edge 7 to a (-30.000 ns), intended edge 11 to d (+25.000 ns)', sMessage)
        self.assertIn('captures on rising edge, expected falling', sMessage)


class TestFallingEdgeCaptureReport(unittest.TestCase):
    '''Owner's report capturing on dac_sclk fall (-setup 3 -start, -hold 4 -start, CRLF line endings).'''

    def setUp(self):
        dConfig11 = utils.read_config_file(os.path.join(os.path.dirname(__file__), 'config_edge11_setup_d_hold_c.yaml'))
        self.paths = checks.load_reports([os.path.join(sReportDir, 'O_DAC_DATA_timing_mcp_falling.rpt')])
        self.data = pin(checks.validate(dConfig11, self.paths), 'O_DAC_DATA')

    def test_falling_capture_parsed(self):
        self.assertEqual({('setup', 0.0, 'rise', 25.0, 'fall'), ('hold', 50.0, 'rise', 25.0, 'fall')},
                         {(p.check, p.launch_edge, p.launch_direction, p.capture_edge, p.capture_direction)
                          for p in self.paths})

    def test_setup_matches_edge_11_to_d(self):
        self.assertEqual('pass', self.data.result('EDG-001').status)

    def test_hold_reported_as_edge_11_to_b(self):
        sMessage = self.data.result('EDG-002').message
        self.assertIn('report checks edge 11 to b (-25.000 ns), intended edge 11 to c (+0.000 ns)', sMessage)
        self.assertIn('captures on falling edge, expected rising', sMessage)


class TestFallingEdgeCaptureIntentFixed(unittest.TestCase):
    '''Owner's corrected intent (setup d, hold b): only the output delays remain for O_DAC_DATA.'''

    def test_only_delays_fail(self):
        dConfig = utils.read_config_file(os.path.join(os.path.dirname(__file__), 'config_edge11_setup_d_hold_b.yaml'))
        oPaths = checks.load_reports([os.path.join(sReportDir, 'O_DAC_DATA_timing_mcp_falling.rpt')])
        oData = pin(checks.validate(dConfig, oPaths), 'O_DAC_DATA')
        self.assertEqual(['DLY-001', 'DLY-002'], [r.check_id for r in oData.results if r.status == checks.FAIL])
        self.assertEqual(['SLK-001', 'SLK-002'], [r.check_id for r in oData.results if r.status == checks.SKIP])


class TestFinalReport(unittest.TestCase):
    '''Owner's report with falling-edge capture, multicycle paths and derived output delays.'''

    def setUp(self):
        dConfig = utils.read_config_file(os.path.join(os.path.dirname(__file__), 'config_edge11_setup_d_hold_b.yaml'))
        oPaths = checks.load_reports([os.path.join(sReportDir, 'O_DAC_DATA_timing_final.rpt')])
        self.data = pin(checks.validate(dConfig, oPaths), 'O_DAC_DATA')

    def test_every_check_passes(self):
        self.assertEqual({checks.PASS}, {r.status for r in self.data.results})
        self.assertEqual(checks.PASS, self.data.status)

    def test_worst_slack(self):
        self.assertEqual('Worst setup slack 17.692 ns at Fast Process Corner.', self.data.result('SLK-001').message)
        self.assertEqual('Worst hold slack 18.736 ns at Fast Process Corner.', self.data.result('SLK-002').message)
