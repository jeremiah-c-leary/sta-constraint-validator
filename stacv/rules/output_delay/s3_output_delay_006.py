'''
:Stage: 3 - board and part
:Applies to: SDR-SYS-O
:Reads: ``output_delay`` of the first hold timing report, the data trace, the source's clock traces to the part and to the device, and the part pin's ``hold``
:Depends on: s2_output_delay_002

The minimum output delay in the timing reports must match the minimum output delay calculated from the traces and part TOML files.
The output delay of the first hold timing report is compared to the calculated value; s2_output_delay_002 has checked every hold timing report gives the same output delay.
If it differs, then the values in the TOML files or the applied timing constraints are incorrect.

The calculation performed is: data trace minimum delay - part hold - source to part clock trace maximum delay + source to device clock trace minimum delay.
A clock source drives the device and the part on their own traces, so the part's clock edge comes the difference of the two clock traces after the device's, which leaves the data that much longer to arrive.

The output delay matches when it is within 0.0005 ns of the calculated output delay, half of the last digit printed in the timing report.

**Result**

When the rule fails, it gives the file and line of the output delay of the first hold timing report:

.. code-block:: text

     O_RMII_TX_EN_timing.rpt:138  Calculated minimum output delay is 0.200ns while actual output delay is -0.800ns

**Likely causes**

* The trace delay values in the traces TOML file are incorrect
* The setup and hold values in the part TOML file are incorrect
* The wrong output delay value was applied in the timing constraints

Refer to the vendor's timing constraints documentation for output delays.
'''

from stacv.rules import port_delay_rules
from stacv.rules import port_delays


RULE_ID = 's3_output_delay_006'
FAILURE_MESSAGE = 'Minimum output delay values in timing reports do not match delays in traces and part definitions.'


def check(oPortProfile):
    '''
    Purpose:  Check minimum output delay values match between configuration and timing reports.
    '''
    return port_delay_rules.check_minimum_delay(oPortProfile, port_delays.calculate_system_synchronous_output, port_delay_rules.OUTPUT_DELAY, RULE_ID, FAILURE_MESSAGE)
