import os

from tests.rules import rule_test_case

# The rules of the methodologies whose clock comes from the part or a clock source, and of double data rate,
# are tested on the VSC8540ET example: its timing reports are a Vivado run of the constraints stacv generates for it.
# The VSC8540ET's files from before its RMII interface was linked by signal; see the fixture's README.
sExampleDir = os.path.join(rule_test_case.sProjectDir, 'tests', 'fixtures', 'vsc8540et')
sTimingReportDir = os.path.join(rule_test_case.sProjectDir, 'example', 'microchip', 'vsc8540et', 'timing_reports')


def read_example_file(sFilename):
    with open(os.path.join(sExampleDir, sFilename)) as oFile:
        return oFile.read()


def replace_text(sText, lReplacements):
    # Each replacement is (old, new); old must be in the text.
    for sOld, sNew in lReplacements:
        if sOld not in sText:
            raise ValueError(f'{sOld!r} is not in the text')
        sText = sText.replace(sOld, sNew)
    return sText


class Vsc8540etRuleTestCase(rule_test_case.RuleTestCase):
    '''
    Runs check on one interface of the VSC8540ET example, with the example's files unless a test changes one.
    The part, traces and interface files are copied beside each other, and the interface reads the example's timing reports,
    or a changed copy of one.
    '''

    sInterface = None
    sPort = None
    sMethodology = None

    def setUp(self):
        rule_test_case.RuleTestCase.setUp(self)
        self.sSuiteName = f'{self.sPort}.{self.sMethodology}'
        self.sInterfaceFile = os.path.join(self.oTempDir.name, f'{self.sInterface}.toml')

    def execute(self, lInterfaceChanges=[], lPartChanges=[], lTracesChanges=[], sReport=None, lReportChanges=[]):
        sInterfaceText = read_example_file(f'{self.sInterface}.toml').replace('$PROJ_DIR', rule_test_case.sProjectDir)
        sInterfaceText = replace_text(sInterfaceText, lInterfaceChanges)
        if sReport is not None:
            sInterfaceText = sInterfaceText.replace(os.path.join(sTimingReportDir, sReport), self.write_changed_report(sReport, lReportChanges))
        rule_test_case.write_file(self.sInterfaceFile, sInterfaceText)
        rule_test_case.write_file(os.path.join(self.oTempDir.name, 'vsc8540et.toml'), replace_text(read_example_file('vsc8540et.toml'), lPartChanges))
        rule_test_case.write_file(os.path.join(self.oTempDir.name, 'traces.toml'), replace_text(read_example_file('traces.toml'), lTracesChanges))
        return self.run_check()

    def write_changed_report(self, sReport, lReportChanges):
        self.sChangedTimingReport = os.path.join(self.oTempDir.name, sReport)
        rule_test_case.write_file(self.sChangedTimingReport, replace_text(read_example_file(os.path.join('timing_reports', sReport)), lReportChanges))
        return self.sChangedTimingReport

    def get_failure_text(self, sRuleId):
        return self.find_testcase(sRuleId).find('failure').text
