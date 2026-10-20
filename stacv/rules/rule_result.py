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

    def is_passed(self):
        return self.status == PASSED

    def is_failed(self):
        return self.status == FAILED

    def is_skipped(self):
        return self.status == SKIPPED
