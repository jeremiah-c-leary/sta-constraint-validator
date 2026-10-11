'''
This module provides a class that will be used to perform operations over multiple rules.
'''

class RuleResultList():

    def __init__(self):
        self.results = []

    def add(self, oResult):
        self.results.append(oResult)

    def all_passed(self):
        for oResult in self.results:
            if not oResult.is_passed():
                return False
        return True

    def get_failing_results(self):
        lFailingTests = []
        for oResult in self.results:
            if not oResult.is_passed():
                lFailingTests.append(oResult)
        return lFailingTests
