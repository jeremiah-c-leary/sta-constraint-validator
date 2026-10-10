'''
:Stage: 2 - across timing reports
:Applies to: SDR-SS-O, DDR-SS-O
:Reads: ``output_delay`` of every hold timing report
:Depends on: none

Every hold timing report must use the same output delay.
Setup timing reports are checked by s2_output_delay_001, because the setup and hold output delays come from the maximum and minimum output delay constraints and are expected to differ.
The output delay is a constraint, not a property of the silicon, so it does not change between process corners.
If it differs, the timing reports were not generated with the same constraints.

**Violation**

The hold timing report at the Fast process corner uses a different output delay than the hold timing report at the Slow process corner:

.. code-block:: text
   :emphasize-lines: 3, 7

     Hold timing report, Fast process corner:
       Path Type:              Min at Fast Process Corner
       Output Delay:           1.000ns

     Hold timing report, Slow process corner:
       Path Type:              Min at Slow Process Corner
       Output Delay:           1.100ns

**Likely causes**

* The timing reports were generated from different implementation runs or design checkpoints, and the constraints changed between them.
* More than one output delay constraint applies to the port, and the timing reports use different ones.

Refer to the vendor's timing constraints documentation for output delays.
'''

from stacv.rules import output_delay_comparisons
from stacv.rules import rule_result


def check(oTimingReportList):
    '''
    Purpose:  Output delays match in every hold timing report.
    '''

    lHoldReports = oTimingReportList.get_hold_reports()
    
    if output_delay_comparisons.output_delays_are_identical(lHoldReports):
        oRuleResult = rule_result.RuleResult('s2_output_delay_002', True, [])
    else:
        lDetail = extract_output_delay_error_detail(lHoldReports)
        oRuleResult = rule_result.RuleResult('s2_output_delay_002', False, lDetail)
    return oRuleResult


def extract_output_delay_error_detail(lHoldReports):
    lDetail = get_output_delay_detail(lHoldReports)
    return format_detail(lDetail)


def format_detail(lDetail):
    lFormattedDetail= []
    for oDetail in lDetail:
        lFormattedDetail.append(f'{oDetail.filename}:{oDetail.line_number}  {oDetail.delay:.3f}ns')
    return lFormattedDetail


def get_output_delay_detail(lHoldReports):
    lDetail = []
    for oHoldReport in lHoldReports:
        lDetail.append(create_detail_information(oHoldReport))
    return lDetail


def create_detail_information(oHoldReport):
    oDetail = DetailInformation()
    oOutputDelayLine = oHoldReport.get_output_delay_line()
    oDetail.filename = oOutputDelayLine.filename
    oDetail.line_number = oOutputDelayLine.line_number
    oDetail.delay = oHoldReport.get_output_delay()
    return oDetail


class DetailInformation():

   def __init__(self, sFilename='', iLineNumber=0, iDelay=0):
       self.filename = sFilename
       self.line_number = iLineNumber
       self.delay = iDelay
