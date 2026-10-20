import unittest

from stacv.results import rule_result


class Test(unittest.TestCase):

    def test_passing_rule_result_has_no_details(self):
        oRuleResult = rule_result.RuleResult('s2_output_delay_002', rule_result.PASSED, [], '')

        self.assertEqual('s2_output_delay_002', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.is_passed())
        self.assertEqual([], oRuleResult.details)

    def test_failing_rule_result_keeps_details_in_order(self):
        lDetails = ['first.rpt:14  1.000ns', 'first.rpt:158  1.100ns']

        oRuleResult = rule_result.RuleResult('s2_output_delay_002', rule_result.FAILED, lDetails, '')

        self.assertEqual('s2_output_delay_002', oRuleResult.rule_id)
        self.assertFalse(oRuleResult.is_passed())
        self.assertEqual(lDetails, oRuleResult.details)

    def test_rule_result_with_passed_status_is_only_passed(self):
        oRuleResult = rule_result.RuleResult('s1_clock_001', rule_result.PASSED, [], '')

        self.assertEqual('s1_clock_001', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.is_passed())
        self.assertFalse(oRuleResult.is_failed())
        self.assertFalse(oRuleResult.is_skipped())
        self.assertEqual([], oRuleResult.details)

    def test_rule_result_with_failed_status_is_only_failed(self):
        lDetails = ['first.rpt:51  path 1', 'first.rpt:117  path 2']

        oRuleResult = rule_result.RuleResult('s2_clock_002', rule_result.FAILED, lDetails, '')

        self.assertEqual('s2_clock_002', oRuleResult.rule_id)
        self.assertFalse(oRuleResult.is_passed())
        self.assertTrue(oRuleResult.is_failed())
        self.assertFalse(oRuleResult.is_skipped())
        self.assertEqual(lDetails, oRuleResult.details)

    def test_rule_result_with_skipped_status_is_only_skipped(self):
        lDetails = ['no hold timing reports found']

        oRuleResult = rule_result.RuleResult('s2_output_delay_002', rule_result.SKIPPED, lDetails, '')

        self.assertEqual('s2_output_delay_002', oRuleResult.rule_id)
        self.assertFalse(oRuleResult.is_passed())
        self.assertFalse(oRuleResult.is_failed())
        self.assertTrue(oRuleResult.is_skipped())
        self.assertEqual(lDetails, oRuleResult.details)
