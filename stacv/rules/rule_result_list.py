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

    def get_number_of_failures(self):
        return len(self.get_failing_results())

    def get_number_of_rules(self):
        return len(self.results)

    def get_number_of_skips(self):
        return len(self.get_skipped_results())

    def get_results(self):
        lResults = []
        for oResult in self.results:
            lResults.append(oResult)
        return lResults

    def get_skipped_results(self):
        lSkippedTests = []
        for oResult in self.results:
            if oResult.is_skipped():
                lSkippedTests.append(oResult)
        return lSkippedTests
