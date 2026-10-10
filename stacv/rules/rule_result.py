'''
The result of checking one rule.
'''


class RuleResult():
    def __init__(self, sRuleId, bPassed, lDetails):
        self.rule_id = sRuleId
        self.passed = bPassed
        self.details = lDetails
