import unittest

from stacv.methodology import stage

from stacv.timing_report import timing_report_list

from tests.methodology.fake_rules import passing_rule
from tests.methodology.fake_rules import second_passing_rule
from tests.methodology.fake_rules import failing_rule

from tests import utils


def get_rule_ids(oStageResult):
    lRuleIds = []
    for oResult in oStageResult.rule_results.results:
        lRuleIds.append(oResult.rule_id)
    return lRuleIds


class Test(unittest.TestCase):

    def setUp(self):
        self.oPortProfile = utils.create_port_profile(timing_report_list.TimingReportList())

    def test_stage_keeps_its_name(self):
        oStage = stage.Stage('stage 1', [passing_rule])

        self.assertEqual('stage 1', oStage.name)

    def test_stage_keeps_its_rules_in_order(self):
        oStage = stage.Stage('stage 1', [passing_rule, failing_rule])

        self.assertEqual([passing_rule, failing_rule], oStage.rules)

    def test_check_returns_stage_result_with_the_stage_name(self):
        oStage = stage.Stage('stage 2', [passing_rule])

        oStageResult = oStage.check(self.oPortProfile)

        self.assertEqual('stage 2', oStageResult.name)

    def test_check_returns_one_result_per_rule_in_rule_order(self):
        oStage = stage.Stage('stage 2', [passing_rule, failing_rule, second_passing_rule])

        oStageResult = oStage.check(self.oPortProfile)

        self.assertEqual(['fake_passing_rule', 'fake_failing_rule', 'fake_second_passing_rule'], get_rule_ids(oStageResult))

    def test_check_runs_every_rule_after_a_failing_rule(self):
        oStage = stage.Stage('stage 2', [failing_rule, second_passing_rule])

        oStageResult = oStage.check(self.oPortProfile)

        self.assertEqual(2, len(oStageResult.rule_results.results))

    def test_check_result_has_failures_when_a_rule_fails(self):
        oStage = stage.Stage('stage 2', [passing_rule, failing_rule])

        oStageResult = oStage.check(self.oPortProfile)

        self.assertTrue(oStageResult.has_failures())

    def test_check_result_has_no_failures_when_every_rule_passes(self):
        oStage = stage.Stage('stage 2', [passing_rule, second_passing_rule])

        oStageResult = oStage.check(self.oPortProfile)

        self.assertFalse(oStageResult.has_failures())

    def test_check_with_no_rules_returns_no_results(self):
        oStage = stage.Stage('stage 3', [])

        oStageResult = oStage.check(self.oPortProfile)

        self.assertEqual([], oStageResult.rule_results.results)

    def test_skip_returns_stage_result_with_the_stage_name(self):
        oStage = stage.Stage('stage 2', [passing_rule])

        oStageResult = oStage.skip('stage 1 failed')

        self.assertEqual('stage 2', oStageResult.name)

    def test_skip_returns_one_skipped_result_per_rule_in_rule_order(self):
        oStage = stage.Stage('stage 2', [passing_rule, failing_rule, second_passing_rule])

        oStageResult = oStage.skip('stage 1 failed')

        for oResult in oStageResult.rule_results.results:
            self.assertTrue(oResult.is_skipped())
        self.assertEqual(['fake_passing_rule', 'fake_failing_rule', 'fake_second_passing_rule'], get_rule_ids(oStageResult))

    def test_skip_gives_the_reason_as_details(self):
        oStage = stage.Stage('stage 2', [passing_rule])

        oStageResult = oStage.skip('stage 1 failed')

        self.assertEqual(['stage 1 failed'], oStageResult.rule_results.results[0].details)

    def test_skip_does_not_run_rules(self):
        oStage = stage.Stage('stage 2', [failing_rule])

        oStageResult = oStage.skip('stage 1 failed')

        self.assertFalse(oStageResult.has_failures())

    def test_skip_with_no_rules_returns_no_results(self):
        oStage = stage.Stage('stage 3', [])

        oStageResult = oStage.skip('stage 1 failed')

        self.assertEqual([], oStageResult.rule_results.results)
