'''
The result of checking one rule.
'''


PASSED = 'passed'
FAILED = 'failed'
SKIPPED = 'skipped'


class RuleResult():
    def __init__(self, sRuleId, sResult, lDetails, sFailureMessage):
        self.rule_id = sRuleId
        self.status = sResult
        self.details = lDetails
        self.failure_message = sFailureMessage

    def is_failed(self):
        return self.status == FAILED

    def is_passed(self):
        return self.status == PASSED

    def is_skipped(self):
        return self.status == SKIPPED


def generate_rule_result(sRuleId, lDetails, sFailureMessage):
    if has_mismatches(lDetails):
        return RuleResult(sRuleId, FAILED, lDetails, sFailureMessage)
    return RuleResult(sRuleId, PASSED, [], '')


def has_mismatches(lDetails):
    return len(lDetails) > 0
