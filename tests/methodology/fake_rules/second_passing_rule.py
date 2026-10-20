'''
Stands in for a rule module in the methodology tests.  It always returns PASSED.
'''

from stacv.results import rule_result

RULE_ID = 'fake_second_passing_rule'


def check(oTimingReportList):
    return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')
