'''
Stands in for a rule module in the methodology tests.  It always returns FAILED.
'''

from stacv.results import rule_result

RULE_ID = 'fake_failing_rule'


def check(oPortProfile):
    return rule_result.RuleResult(RULE_ID, rule_result.FAILED, [], 'FAILED')
