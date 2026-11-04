'''
:Stage: 3 - board and part
:Applies to: SDR-SYS-O
:Reads: ``output_delay`` of the first setup timing report, the data trace, the source's clock traces to the part and to the device, and the part pin's ``setup``
:Depends on: s2_output_delay_001

The maximum output delay in the timing reports must match the maximum output delay calculated from the traces and part TOML files.
The output delay of the first setup timing report is compared to the calculated value; s2_output_delay_001 has checked every setup timing report gives the same output delay.
If it differs, then the values in the TOML files or the applied timing constraints are incorrect.

The calculation performed is: data trace maximum delay + part setup - source to part clock trace minimum delay + source to device clock trace maximum delay.
A clock source drives the device and the part on their own traces, so the part's clock edge comes the difference of the two clock traces after the device's, which leaves the data that much longer to arrive.

The output delay matches when it is within 0.0005 ns of the calculated output delay, half of the last digit printed in the timing report.

**Result**

When the rule fails, it gives the file and line of the output delay of the first setup timing report:

.. code-block:: text

     O_RMII_TX_EN_timing.rpt:24  Calculated maximum output delay is 7.200ns while actual output delay is 6.200ns

**Likely causes**

* The trace delay values in the traces TOML file are incorrect
* The setup and hold values in the part TOML file are incorrect
* The wrong output delay value was applied in the timing constraints

Refer to the vendor's timing constraints documentation for output delays.
'''

from stacv.rules import port_delay_rules
from stacv.rules import port_delays


RULE_ID = 's3_output_delay_005'
FAILURE_MESSAGE = 'Maximum output delay values in timing reports do not match delays in traces and part definitions.'


def check(oPortProfile):
    '''
    Purpose:  Check maximum output delay values match between configuration and timing reports.
    '''
    return port_delay_rules.check_maximum_delay(oPortProfile, port_delays.calculate_system_synchronous_output, port_delay_rules.OUTPUT_DELAY, RULE_ID, FAILURE_MESSAGE)
