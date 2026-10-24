'''
:Stage: 5 - slack
:Applies to: all
:Reads: ``slack`` of every hold timing report
:Depends on: none

The hold slack in every hold timing report must be zero or positive.
Every hold timing report is checked, at every process corner.
A slack of zero passes, and no tolerance is applied.
This rule runs after the stages that check the timing reports against the intended timing, so a negative slack is a real hold violation of the interface and not a constraint error.

**Violation**

The hold timing report gives a negative slack:

.. code-block:: text
   :emphasize-lines: 1

     Slack (VIOLATED) :        -0.012ns  (arrival time - required time)
       Source:                 q_spi_output_data_reg/C
       ...
       Path Type:              Min at Fast Process Corner

**Result**

When the rule fails, it lists each hold timing report with a negative slack, with the file and line where the timing report gives the slack:

.. code-block:: text

     O_DAC_DATA_timing.rpt:14  hold slack -0.012ns

**Likely causes**

* The data path from the launch register to the port is too fast compared with the forwarded clock path.
* The part hold time or the board trace delays need more delay on the data than the device provides.
* The clock is forwarded with a different delay than the data, for example through a different type of output buffer.
'''

from stacv.results import rule_result


RULE_ID = 's5_slack_002'
FAILURE_MESSAGE = 'Hold slack in timing reports is negative.'


def check(oPortProfile):
    '''
    Purpose:  Checks the hold slack in the hold timing reports is not negative.
    '''
    lDetails = []

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)
