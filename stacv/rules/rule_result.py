'''
The result of checking one rule.
'''


PASSED = 'passed'
FAILED = 'failed'
SKIPPED = 'skipped'


class RuleResult():
    def __init__(self, sRuleId, sResult, lDetails):
        self.rule_id = sRuleId
        self.result = sResult
        self.details = lDetails

    def is_passed(self):
        return self.result == PASSED

    def is_failed(self):
        return self.result == FAILED

    def is_skipped(self):
        return self.result == SKIPPED
