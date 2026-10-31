'''
The result of a port whose analysis is deferred.
'''

from stacv.results import rule_result
from stacv.results import rule_result_list

RULE_ID = 'deferred'
MESSAGE = 'port is deferred'


class DeferredPortResult():

    def __init__(self, oPort):
        self.port = oPort
        self.rule_results = rule_result_list.RuleResultList()
        self.rule_results.add_result(rule_result.RuleResult(RULE_ID, rule_result.SKIPPED, [MESSAGE], ''))

    def get_identifier(self):
        if self.port.methodology is None:
            return self.port.name
        return self.port.name + '.' + self.port.methodology

    def get_methodology(self):
        if self.port.methodology is None:
            return ''
        return self.port.methodology

    def get_number_of_failures(self):
        return self.get_results().get_number_of_failures()

    def get_number_of_rules(self):
        return self.get_results().get_number_of_rules()

    def get_number_of_skips(self):
        return self.get_results().get_number_of_skips()

    def get_results(self):
        return self.rule_results

    def has_failures(self):
        return False

    def is_deferred(self):
        return True
