'''
Builds MethodologyResults for the results tests by checking fake rules.
'''

from stacv.methodology import methodology
from stacv.methodology import stage

from stacv.timing_report import timing_report_list

from tests.methodology.fake_rules import passing_rule
from tests.methodology.fake_rules import failing_rule


def build_passing_methodology_results():
    return check_rules([passing_rule])


def build_failing_methodology_results():
    return check_rules([passing_rule, failing_rule])


def check_rules(lRules):
    oMethodology = methodology.Methodology()
    oMethodology.stages = [stage.Stage('stage 0', lRules)]
    return oMethodology.check(timing_report_list.TimingReportList())
