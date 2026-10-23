import os
import unittest

from stacv.methodology import methodology
from stacv.methodology import sdr_source_synchronous_output

from stacv.timing_report import timing_report_file

from stacv.timing_report.xilinx import vivado

from tests import utils

sTestDir = os.path.dirname(__file__)
sReportDir = os.path.join(sTestDir, '..', 'timing_report', 'parse', 'vivado')

oPassingFile = timing_report_file.TimingReportFile('O_DAC_DATA_timing.rpt', utils.read_file(os.path.join(sReportDir, 'O_DAC_DATA_timing.rpt')))


def get_stage_names(oMethodology):
    lStageNames = []
    for oStage in oMethodology.stages:
        lStageNames.append(oStage.name)
    return lStageNames


def get_rule_ids(oStage):
    lRuleIds = []
    for mRule in oStage.rules:
        lRuleIds.append(mRule.RULE_ID)
    return lRuleIds


class Test(unittest.TestCase):

    def setUp(self):
        self.oMethodology = sdr_source_synchronous_output.SdrSourceSynchronousOutput()

    def test_is_a_methodology(self):
        self.assertIsInstance(self.oMethodology, methodology.Methodology)

    def test_stages_are_in_order(self):
        self.assertEqual(['stage 0', 'stage 1', 'stage 2', 'stage 3', 'stage 4'], get_stage_names(self.oMethodology))

    def test_stage_0_rules(self):
        lExpected = []
        lExpected.append('s0_timing_report_001')
        lExpected.append('s0_timing_report_002')
        lExpected.append('s0_trace_001')

        self.assertEqual(lExpected, get_rule_ids(self.oMethodology.stages[0]))

    def test_stage_1_rules(self):
        lExpected = []
        lExpected.append('s1_clock_001')

        self.assertEqual(lExpected, get_rule_ids(self.oMethodology.stages[1]))

    def test_stage_2_rules(self):
        lExpected = []
        lExpected.append('s2_clock_001')
        lExpected.append('s2_clock_002')
        lExpected.append('s2_data_path_001')
        lExpected.append('s2_output_delay_001')
        lExpected.append('s2_output_delay_002')

        self.assertEqual(lExpected, get_rule_ids(self.oMethodology.stages[2]))

    def test_stage_3_rules(self):
        lExpected = []
        lExpected.append('s3_output_delay_001')
        lExpected.append('s3_output_delay_002')

        self.assertEqual(lExpected, get_rule_ids(self.oMethodology.stages[3]))

    @unittest.skip('Propose this can be deleted as the cost of testing has increased due to the need for trace and part test data.  The tests at the check level are sufficient to cover this test.')
    def test_check_passes_every_rule_on_dac_timing_reports(self):
        oTimingReports = vivado.parse_timing_report(oPassingFile)

        oMethodologyResult = self.oMethodology.check(utils.create_port_profile(oTimingReports))

        self.assertFalse(oMethodologyResult.has_failures())
        lResults = []
        for oStageResult in oMethodologyResult.stage_results:
            lResults.extend(oStageResult.rule_results.results)
        self.assertEqual(8, len(lResults))
        for oResult in lResults:
            self.assertTrue(oResult.is_passed())
