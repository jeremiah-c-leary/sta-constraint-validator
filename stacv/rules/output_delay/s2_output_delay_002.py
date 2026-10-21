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


RULE_ID = 's2_output_delay_002'
FAILURE_MESSAGE = 'Hold output delays over all hold reports are not the same value.'


def check(oPortProfile):
    '''
    Purpose:  Output delays match in every hold timing report.
    '''
    
    lHoldReports = oPortProfile.timing_reports.get_hold_reports()
    return output_delay_comparisons.check_output_delays_match(lHoldReports, RULE_ID, FAILURE_MESSAGE)
