import unittest

from stacv.methodology import stage

from stacv.timing_report import timing_report_list

from tests.methodology.fake_rules import passing_rule
from tests.methodology.fake_rules import second_passing_rule
from tests.methodology.fake_rules import failing_rule


class Test(unittest.TestCase):

    def setUp(self):
        self.oTimingReports = timing_report_list.TimingReportList()

    def test_stage_keeps_its_name(self):
        oStage = stage.Stage('stage 1', [passing_rule])

        self.assertEqual('stage 1', oStage.name)

    def test_stage_keeps_its_rules_in_order(self):
        oStage = stage.Stage('stage 1', [passing_rule, failing_rule])

        self.assertEqual([passing_rule, failing_rule], oStage.rules)

    def test_check_returns_one_result_per_rule_in_rule_order(self):
        oStage = stage.Stage('stage 2', [passing_rule, failing_rule, second_passing_rule])

        oRuleResults = oStage.check(self.oTimingReports)

        lRuleIds = []
        for oResult in oRuleResults.results:
            lRuleIds.append(oResult.rule_id)
        self.assertEqual(['fake_passing_rule', 'fake_failing_rule', 'fake_second_passing_rule'], lRuleIds)

    def test_check_runs_every_rule_after_a_failing_rule(self):
        oStage = stage.Stage('stage 2', [failing_rule, second_passing_rule])

        oRuleResults = oStage.check(self.oTimingReports)

        self.assertTrue(oRuleResults.has_failures())
        self.assertEqual(2, len(oRuleResults.results))

    def test_check_with_no_rules_returns_no_results(self):
        oStage = stage.Stage('stage 3', [])

        oRuleResults = oStage.check(self.oTimingReports)

        self.assertEqual([], oRuleResults.results)

    def test_skip_returns_one_skipped_result_per_rule_in_rule_order(self):
        oStage = stage.Stage('stage 2', [passing_rule, failing_rule, second_passing_rule])

        oRuleResults = oStage.skip('stage 1 failed')

        lRuleIds = []
        for oResult in oRuleResults.results:
            lRuleIds.append(oResult.rule_id)
            self.assertTrue(oResult.is_skipped())
        self.assertEqual(['fake_passing_rule', 'fake_failing_rule', 'fake_second_passing_rule'], lRuleIds)

    def test_skip_gives_the_reason_as_details(self):
        oStage = stage.Stage('stage 2', [passing_rule])

        oRuleResults = oStage.skip('stage 1 failed')

        self.assertEqual(['stage 1 failed'], oRuleResults.results[0].details)

    def test_skip_does_not_run_rules(self):
        oStage = stage.Stage('stage 2', [failing_rule])

        oRuleResults = oStage.skip('stage 1 failed')

        self.assertFalse(oRuleResults.has_failures())

    def test_skip_with_no_rules_returns_no_results(self):
        oStage = stage.Stage('stage 3', [])

        oRuleResults = oStage.skip('stage 1 failed')

        self.assertEqual([], oRuleResults.results)
