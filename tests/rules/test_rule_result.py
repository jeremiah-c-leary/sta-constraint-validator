
import unittest

from stacv.rules import rule_result


class Test(unittest.TestCase):

    def test_passing_rule_result_has_no_details(self):
        oRuleResult = rule_result.RuleResult('s2_output_delay_002', True, [])

        self.assertEqual('s2_output_delay_002', oRuleResult.rule_id)
        self.assertTrue(oRuleResult.passed)
        self.assertEqual([], oRuleResult.details)

    def test_failing_rule_result_keeps_details_in_order(self):
        lDetails = ['first.rpt:14  1.000ns', 'first.rpt:158  1.100ns']

        oRuleResult = rule_result.RuleResult('s2_output_delay_002', False, lDetails)

        self.assertEqual('s2_output_delay_002', oRuleResult.rule_id)
        self.assertFalse(oRuleResult.passed)
        self.assertEqual(lDetails, oRuleResult.details)
