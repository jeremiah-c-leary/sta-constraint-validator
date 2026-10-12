'''
Stands in for a rule module in the methodology tests.  It always returns FAILED.
'''

from stacv.rules import rule_result

RULE_ID = 'fake_failing_rule'


def check(oTimingReportList):
    return rule_result.RuleResult(RULE_ID, rule_result.FAILED, [])
