'''
Contains functions to assist with clock rules.
'''

from stacv.results import rule_result


def generate_rule_result(sRuleId, lDetails, sFailureMessage):
    if has_mismatches(lDetails):
        return rule_result.RuleResult(sRuleId, rule_result.FAILED, lDetails, sFailureMessage)
    return rule_result.RuleResult(sRuleId, rule_result.PASSED, [], '')


def has_mismatches(lDetails):
    return len(lDetails) > 0
