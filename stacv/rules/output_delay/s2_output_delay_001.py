'''
:Stage: 2 - across timing reports
:Applies to: SDR-SS-O, DDR-SS-O
:Reads: ``output_delay`` of every setup timing report
:Depends on: none

Every setup timing report must use the same output delay.
Hold timing reports are checked by s2_output_delay_002, because the setup and hold output delays come from the maximum and minimum output delay constraints and are expected to differ.
The output delay is a constraint, not a property of the silicon, so it does not change between process corners.
If it differs, the timing reports were not generated with the same constraints.

**Violation**

The setup timing report at the Fast process corner uses a different output delay than the setup timing report at the Slow process corner:

.. code-block:: text
   :emphasize-lines: 3, 7

     Setup timing report, Fast process corner:
       Path Type:              Max at Fast Process Corner
       Output Delay:           2.000ns

     Setup timing report, Slow process corner:
       Path Type:              Max at Slow Process Corner
       Output Delay:           2.500ns

**Likely causes**

* The timing reports were generated from different implementation runs or design checkpoints, and the constraints changed between them.
* More than one output delay constraint applies to the port, and the timing reports use different ones.

Refer to the vendor's timing constraints documentation for output delays.
'''

from stacv.rules import delay_comparisons


RULE_ID = 's2_output_delay_001'
FAILURE_MESSAGE = 'Setup output delays over all setup reports are not the same value.'


def check(oPortProfile):
    '''
    Purpose:  Output delays match in every setup timing report.
    '''

    lSetupReports = oPortProfile.timing_reports.get_setup_reports()
    return delay_comparisons.check_delays_match(lSetupReports, delay_comparisons.OUTPUT_DELAY, RULE_ID, FAILURE_MESSAGE)
