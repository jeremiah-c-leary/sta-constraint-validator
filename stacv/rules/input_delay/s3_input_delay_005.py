'''
:Stage: 3 - board and part
:Applies to: SDR-SYS-I
:Reads: ``input_delay`` of the first setup timing report, the source's clock traces to the part and to the device, the data trace, and the part pin's ``cko_max``, or ``valid_before``
:Depends on: s2_input_delay_001

The maximum input delay in the timing reports must match the maximum input delay calculated from the traces and part TOML files.
The input delay of the first setup timing report is compared to the calculated value; s2_input_delay_001 has checked every setup timing report gives the same input delay.
If it differs, then the values in the TOML files or the applied timing constraints are incorrect.

The calculation performed is: source to part clock trace maximum delay - source to device clock trace minimum delay + part clock to out maximum + data trace maximum delay.
A clock source drives the device and the part on their own traces, so the part's clock edge comes the difference of the two clock traces after the device's, and the part launches the data from that edge.

The input delay matches when it is within 0.0005 ns of the calculated input delay, half of the last digit printed in the timing report.

**Result**

When the rule fails, it gives the file and line of the input delay of the first setup timing report:

.. code-block:: text

     I_RMII_CRS_DV_timing.rpt:24  Calculated maximum input delay is 15.300ns while actual input delay is 14.300ns

**Likely causes**

* The trace delay values in the traces TOML file are incorrect
* The clock to out values in the part TOML file are incorrect
* The wrong input delay value was applied in the timing constraints

Refer to the vendor's timing constraints documentation for input delays.
'''

from stacv.rules import port_delay_rules
from stacv.rules import port_delays


RULE_ID = 's3_input_delay_005'
FAILURE_MESSAGE = 'Maximum input delay values in timing reports do not match delays in traces and part definitions.'


def check(oPortProfile):
    '''
    Purpose:  Check maximum input delay values match between configuration and timing reports.
    '''
    return port_delay_rules.check_maximum_delay(oPortProfile, port_delays.calculate_system_synchronous_input, port_delay_rules.INPUT_DELAY, RULE_ID, FAILURE_MESSAGE)
