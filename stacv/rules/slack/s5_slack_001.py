'''
:Stage: 5 - slack
:Applies to: all
:Reads: ``slack`` of every setup timing report
:Depends on: none

The setup slack in every setup timing report must be zero or positive.
Every setup timing report is checked, at every process corner.
A slack of zero passes, and no tolerance is applied.
This rule runs after the stages that check the timing reports against the intended timing, so a negative slack is a real setup violation of the interface and not a constraint error.

**Violation**

The setup timing report gives a negative slack:

.. code-block:: text
   :emphasize-lines: 1

     Slack (VIOLATED) :        -0.012ns  (required time - arrival time)
       Source:                 q_spi_output_data_reg/C
       ...
       Path Type:              Max at Fast Process Corner

**Result**

When the rule fails, it lists each setup timing report with a negative slack, with the file and line where the timing report gives the slack:

.. code-block:: text

     O_DAC_DATA_timing.rpt:75  setup slack -0.012ns

**Likely causes**

* The data path from the launch register to the port is too slow, for example a register that is not placed in the I/O block.
* The part setup time or the board trace delays leave too little of the clock period for the device.
* The interface clock is too fast for the part and the board.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's5_slack_001'
FAILURE_MESSAGE = 'Setup slack in timing reports is negative.'


def check(oPortProfile):
    '''
    Purpose:  Checks the setup slack in the setup timing reports is not negative.
    '''
    lDetails = get_negative_setup_slacks(oPortProfile)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_negative_setup_slacks(oPortProfile):
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.get_setup_reports():
        if is_negative(oTimingReport.slack):
            sErrorMessage = generate_error_message(oTimingReport)
            lDetails.append(sErrorMessage)
    return lDetails


def is_negative(fSlack):
    return fSlack < 0.0


def generate_error_message(oTimingReport):
    sMessage = f'setup slack {oTimingReport.slack:.3f}ns'
    return rule_details.format_detail(oTimingReport.slack_line, sMessage)
