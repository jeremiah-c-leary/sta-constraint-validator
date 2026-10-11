'''
This module provides a class that will be used to perform operations over multiple rules.
'''

class RuleResultList():

    def __init__(self):
        self.results = []

    def add_result(self, oResult):
        self.results.append(oResult)

    def add_result_list(self, lResults):
        self.results.extend(lResults.results)

    def has_failures(self):
        for oResult in self.results:
            if oResult.is_failed():
                return True
        return False

    def get_failing_results(self):
        lFailingTests = []
        for oResult in self.results:
            if oResult.is_failed():
                lFailingTests.append(oResult)
        return lFailingTests
