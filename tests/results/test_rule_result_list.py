import unittest

from stacv.results import rule_result
from stacv.results import rule_result_list


class Test(unittest.TestCase):

    def setUp(self):
        self.oFirstPassingResult = rule_result.RuleResult('s1_clock_001', rule_result.PASSED, [], '')
        self.oSecondPassingResult = rule_result.RuleResult('s2_clock_001', rule_result.PASSED, [], '')
        self.oFailingResult = rule_result.RuleResult('s2_clock_002', rule_result.FAILED, ['first.rpt:51  path 1', 'first.rpt:117  path 2'], '')
        self.oSecondFailingResult = rule_result.RuleResult('s2_data_path_001', rule_result.FAILED, ['first.rpt:203  path 3'], '')
        self.oSkippedResult = rule_result.RuleResult('s2_output_delay_002', rule_result.SKIPPED, ['no hold timing reports found'], '')

    def test_new_rule_result_list_is_empty(self):
        oRuleResults = rule_result_list.RuleResultList()

        self.assertEqual([], oRuleResults.results)

    def test_add_keeps_results_in_order(self):
        oRuleResults = rule_result_list.RuleResultList()

        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oFailingResult)
        oRuleResults.add_result(self.oSecondPassingResult)

        lExpected = [self.oFirstPassingResult, self.oFailingResult, self.oSecondPassingResult]
        self.assertEqual(lExpected, oRuleResults.results)

    def test_has_no_failures_when_every_result_passed(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oSecondPassingResult)

        self.assertFalse(oRuleResults.has_failures())

    def test_has_failures_when_one_result_failed(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oFailingResult)
        oRuleResults.add_result(self.oSecondPassingResult)

        self.assertTrue(oRuleResults.has_failures())

    def test_empty_rule_result_list_has_no_failures(self):
        oRuleResults = rule_result_list.RuleResultList()

        self.assertFalse(oRuleResults.has_failures())

    def test_skipped_result_is_not_a_failure(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oSkippedResult)

        self.assertFalse(oRuleResults.has_failures())

    def test_get_failing_results_returns_only_failing_results_in_order(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oFailingResult)
        oRuleResults.add_result(self.oSecondPassingResult)
        oRuleResults.add_result(self.oSecondFailingResult)

        lExpected = [self.oFailingResult, self.oSecondFailingResult]
        self.assertEqual(lExpected, oRuleResults.get_failing_results())

    def test_get_failing_results_is_empty_when_every_result_passed(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oSecondPassingResult)

        self.assertEqual([], oRuleResults.get_failing_results())

    def test_get_failing_results_does_not_change_results(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oFailingResult)

        oRuleResults.get_failing_results()

        lExpected = [self.oFirstPassingResult, self.oFailingResult]
        self.assertEqual(lExpected, oRuleResults.results)

    def test_get_failing_results_does_not_return_skipped_results(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add_result(self.oFirstPassingResult)
        oRuleResults.add_result(self.oSkippedResult)
        oRuleResults.add_result(self.oFailingResult)

        lExpected = [self.oFailingResult]
        self.assertEqual(lExpected, oRuleResults.get_failing_results())

    def test_add_results_appends_other_results_after_existing_results_in_order(self):
        oStageZeroResults = rule_result_list.RuleResultList()
        oStageZeroResults.add_result(self.oFirstPassingResult)
        oStageOneResults = rule_result_list.RuleResultList()
        oStageOneResults.add_result(self.oFailingResult)
        oStageOneResults.add_result(self.oSecondPassingResult)

        oStageZeroResults.add_result_list(oStageOneResults)

        lExpected = [self.oFirstPassingResult, self.oFailingResult, self.oSecondPassingResult]
        self.assertEqual(lExpected, oStageZeroResults.results)

    def test_add_results_does_not_change_other_results(self):
        oStageZeroResults = rule_result_list.RuleResultList()
        oStageZeroResults.add_result(self.oFirstPassingResult)
        oStageOneResults = rule_result_list.RuleResultList()
        oStageOneResults.add_result(self.oFailingResult)

        oStageZeroResults.add_result_list(oStageOneResults)

        lExpected = [self.oFailingResult]
        self.assertEqual(lExpected, oStageOneResults.results)
