import unittest

from stacv.methodology import methodology
from stacv.methodology import stage

from stacv.timing_report import timing_report_list

from tests.methodology.fake_rules import passing_rule
from tests.methodology.fake_rules import second_passing_rule
from tests.methodology.fake_rules import failing_rule


class Test(unittest.TestCase):

    def setUp(self):
        self.oTimingReports = timing_report_list.TimingReportList()

    def test_check_runs_every_stage_in_order_when_no_stage_fails(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [second_passing_rule]))
        oMethodology = methodology.Methodology()
        oMethodology.stages = lStages

        oRuleResults = oMethodology.check(self.oTimingReports)

        lRuleIds = []
        for oResult in oRuleResults.results:
            lRuleIds.append(oResult.rule_id)
            self.assertTrue(oResult.is_passed())
        self.assertEqual(['fake_passing_rule', 'fake_second_passing_rule'], lRuleIds)

    def test_check_runs_every_rule_in_the_failing_stage(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [failing_rule, passing_rule]))
        oMethodology = methodology.Methodology()
        oMethodology.stages = lStages

        oRuleResults = oMethodology.check(self.oTimingReports)

        self.assertTrue(oRuleResults.results[0].is_failed())
        self.assertTrue(oRuleResults.results[1].is_passed())

    def test_check_skips_stages_after_a_failing_stage(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [failing_rule]))
        lStages.append(stage.Stage('stage 2', [second_passing_rule]))
        oMethodology = methodology.Methodology()
        oMethodology.stages = lStages

        oRuleResults = oMethodology.check(self.oTimingReports)

        self.assertTrue(oRuleResults.results[0].is_passed())
        self.assertTrue(oRuleResults.results[1].is_failed())
        self.assertTrue(oRuleResults.results[2].is_skipped())
        self.assertEqual(['stage 1 failed'], oRuleResults.results[2].details)

    def test_check_names_the_failing_stage_in_every_later_skip(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [failing_rule]))
        lStages.append(stage.Stage('stage 1', [passing_rule]))
        lStages.append(stage.Stage('stage 2', [second_passing_rule]))
        oMethodology = methodology.Methodology()
        oMethodology.stages = lStages

        oRuleResults = oMethodology.check(self.oTimingReports)

        self.assertEqual(['stage 0 failed'], oRuleResults.results[1].details)
        self.assertEqual(['stage 0 failed'], oRuleResults.results[2].details)

    def test_check_lists_every_rule_once_when_a_stage_fails(self):
        lStages = []
        lStages.append(stage.Stage('stage 0', [passing_rule]))
        lStages.append(stage.Stage('stage 1', [failing_rule]))
        lStages.append(stage.Stage('stage 2', [second_passing_rule]))
        oMethodology = methodology.Methodology()
        oMethodology.stages = lStages

        oRuleResults = oMethodology.check(self.oTimingReports)

        lRuleIds = []
        for oResult in oRuleResults.results:
            lRuleIds.append(oResult.rule_id)
        self.assertEqual(['fake_passing_rule', 'fake_failing_rule', 'fake_second_passing_rule'], lRuleIds)

    def test_check_with_no_stages_returns_no_results(self):
        oMethodology = methodology.Methodology()

        oRuleResults = oMethodology.check(self.oTimingReports)

        self.assertEqual([], oRuleResults.results)
