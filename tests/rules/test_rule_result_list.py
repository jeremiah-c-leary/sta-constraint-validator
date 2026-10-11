import unittest

from stacv.rules import rule_result
from stacv.rules import rule_result_list


class Test(unittest.TestCase):

    def setUp(self):
        self.oFirstPassingResult = rule_result.RuleResult('s1_clock_001', rule_result.PASSED, [])
        self.oSecondPassingResult = rule_result.RuleResult('s2_clock_001', rule_result.PASSED, [])
        self.oFailingResult = rule_result.RuleResult('s2_clock_002', rule_result.FAILED, ['first.rpt:51  path 1', 'first.rpt:117  path 2'])
        self.oSecondFailingResult = rule_result.RuleResult('s2_data_path_001', rule_result.FAILED, ['first.rpt:203  path 3'])

    def test_new_rule_result_list_is_empty(self):
        oRuleResults = rule_result_list.RuleResultList()

        self.assertEqual([], oRuleResults.results)

    def test_add_keeps_results_in_order(self):
        oRuleResults = rule_result_list.RuleResultList()

        oRuleResults.add(self.oFirstPassingResult)
        oRuleResults.add(self.oFailingResult)
        oRuleResults.add(self.oSecondPassingResult)

        lExpected = [self.oFirstPassingResult, self.oFailingResult, self.oSecondPassingResult]
        self.assertEqual(lExpected, oRuleResults.results)

    def test_all_passed_when_every_result_passed(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add(self.oFirstPassingResult)
        oRuleResults.add(self.oSecondPassingResult)

        self.assertTrue(oRuleResults.all_passed())

    def test_not_all_passed_when_one_result_failed(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add(self.oFirstPassingResult)
        oRuleResults.add(self.oFailingResult)
        oRuleResults.add(self.oSecondPassingResult)

        self.assertFalse(oRuleResults.all_passed())

    def test_empty_rule_result_list_has_all_passed(self):
        oRuleResults = rule_result_list.RuleResultList()

        self.assertTrue(oRuleResults.all_passed())

    def test_get_failing_results_returns_only_failing_results_in_order(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add(self.oFirstPassingResult)
        oRuleResults.add(self.oFailingResult)
        oRuleResults.add(self.oSecondPassingResult)
        oRuleResults.add(self.oSecondFailingResult)

        lExpected = [self.oFailingResult, self.oSecondFailingResult]
        self.assertEqual(lExpected, oRuleResults.get_failing_results())

    def test_get_failing_results_is_empty_when_every_result_passed(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add(self.oFirstPassingResult)
        oRuleResults.add(self.oSecondPassingResult)

        self.assertEqual([], oRuleResults.get_failing_results())

    def test_get_failing_results_does_not_change_results(self):
        oRuleResults = rule_result_list.RuleResultList()
        oRuleResults.add(self.oFirstPassingResult)
        oRuleResults.add(self.oFailingResult)

        oRuleResults.get_failing_results()

        lExpected = [self.oFirstPassingResult, self.oFailingResult]
        self.assertEqual(lExpected, oRuleResults.results)
