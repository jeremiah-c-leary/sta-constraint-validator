import unittest

from stacv.methodology import methodology
from stacv.methodology import stage

from stacv.timing_report import timing_report_list

from tests.methodology.fake_rules import passing_rule
from tests.methodology.fake_rules import second_passing_rule
from tests.methodology.fake_rules import failing_rule

from tests import utils


def get_stage_names(oMethodologyResult):
    lStageNames = []
    for oStageResult in oMethodologyResult.stage_results:
        lStageNames.append(oStageResult.name)
    return lStageNames


def get_rule_ids(oMethodologyResult):
    lRuleIds = []
    for oStageResult in oMethodologyResult.stage_results:
        for oResult in oStageResult.rule_results.results:
            lRuleIds.append(oResult.rule_id)
    return lRuleIds


def get_first_result_of_stage(oMethodologyResult, iStage):
    return oMethodologyResult.stage_results[iStage].rule_results.results[0]


class Test(unittest.TestCase):

    def setUp(self):
        self.oPortProfile = utils.create_port_profile(timing_report_list.TimingReportList())

    def check_stages(self, lStages):
        oMethodology = methodology.Methodology()
        oMethodology.stages = lStages
        return oMethodology.check(self.oPortProfile)

    def test_check_returns_one_stage_result_per_stage_in_order(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [second_passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertEqual(['stage 0', 'stage 1'], get_stage_names(oMethodologyResult))

    def test_check_returns_a_stage_result_for_every_skipped_stage(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [failing_rule]))
        lStages.append(stage.Stage('stage 1', [passing_rule]))
        lStages.append(stage.Stage('stage 2', [second_passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertEqual(['stage 0', 'stage 1', 'stage 2'], get_stage_names(oMethodologyResult))

    def test_check_runs_every_stage_in_order_when_no_stage_fails(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [second_passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertTrue(get_first_result_of_stage(oMethodologyResult, 0).is_passed())
        self.assertTrue(get_first_result_of_stage(oMethodologyResult, 1).is_passed())
        self.assertEqual(['fake_passing_rule', 'fake_second_passing_rule'], get_rule_ids(oMethodologyResult))

    def test_check_runs_every_rule_in_the_failing_stage(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [failing_rule, passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        lResults = oMethodologyResult.stage_results[0].rule_results.results
        self.assertTrue(lResults[0].is_failed())
        self.assertTrue(lResults[1].is_passed())

    def test_check_skips_stages_after_a_failing_stage(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [failing_rule]))
        lStages.append(stage.Stage('stage 2', [second_passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertTrue(get_first_result_of_stage(oMethodologyResult, 0).is_passed())
        self.assertTrue(get_first_result_of_stage(oMethodologyResult, 1).is_failed())
        self.assertTrue(get_first_result_of_stage(oMethodologyResult, 2).is_skipped())
        self.assertEqual(['stage 1 failed'], get_first_result_of_stage(oMethodologyResult, 2).details)

    def test_check_names_the_failing_stage_in_every_later_skip(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [failing_rule]))
        lStages.append(stage.Stage('stage 1', [passing_rule]))
        lStages.append(stage.Stage('stage 2', [second_passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertEqual(['stage 0 failed'], get_first_result_of_stage(oMethodologyResult, 1).details)
        self.assertEqual(['stage 0 failed'], get_first_result_of_stage(oMethodologyResult, 2).details)

    def test_check_lists_every_rule_once_when_a_stage_fails(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [failing_rule]))
        lStages.append(stage.Stage('stage 2', [second_passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertEqual(['fake_passing_rule', 'fake_failing_rule', 'fake_second_passing_rule'], get_rule_ids(oMethodologyResult))

    def test_check_result_has_failures_when_a_stage_fails(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [failing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertTrue(oMethodologyResult.has_failures())

    def test_check_result_has_no_failures_when_every_stage_passes(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [second_passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        self.assertFalse(oMethodologyResult.has_failures())

    def test_check_result_gives_failing_results_in_rule_order(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [failing_rule, second_passing_rule, failing_rule]))
        lStages.append(stage.Stage('stage 2', [passing_rule]))

        oMethodologyResult = self.check_stages(lStages)

        lRuleIds = []
        for oResult in oMethodologyResult.get_failing_results():
            lRuleIds.append(oResult.rule_id)
        self.assertEqual(['fake_failing_rule', 'fake_failing_rule'], lRuleIds)

    def test_check_with_no_stages_returns_no_stage_results(self):
        oMethodologyResult = self.check_stages([])

        self.assertEqual([], oMethodologyResult.stage_results)
        self.assertFalse(oMethodologyResult.has_failures())
