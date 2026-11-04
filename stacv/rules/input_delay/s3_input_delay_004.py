'''
:Stage: 3 - board and part
:Applies to: SDR-SS-I, DDR-SS-I-SE, DDR-SS-I-NE
:Reads: ``input_delay`` of the first hold timing report, trace delays, and the part pin's ``cko_min``, or ``valid_after``
:Depends on: s2_input_delay_002

The minimum input delay in the timing reports must match the minimum input delay calculated from the traces and part TOML files.
The input delay of the first hold timing report is compared to the calculated value; s2_input_delay_002 has checked every hold timing report gives the same input delay.
If it differs, then the values in the TOML files or the applied timing constraints are incorrect.

The calculation performed is: part clock to out minimum + data trace minimum delay - clock trace maximum delay.
The part launches the data on its own clock, and both travel to the device: the input delay is measured from the clock at the device's clock port, so the clock trace is subtracted.

The input delay matches when it is within 0.0005 ns of the calculated input delay, half of the last digit printed in the timing report.

**Result**

When the rule fails, it gives the file and line of the input delay of the first hold timing report:

.. code-block:: text

     I_MII_RX_DV_timing.rpt:138  Calculated minimum input delay is 10.600ns while actual input delay is 9.600ns

**Likely causes**

* The trace delay values in the traces TOML file are incorrect
* The clock to out values in the part TOML file are incorrect
* The wrong input delay value was applied in the timing constraints

Refer to the vendor's timing constraints documentation for input delays.
'''

from stacv.rules import port_delay_rules
from stacv.rules import port_delays


RULE_ID = 's3_input_delay_004'
FAILURE_MESSAGE = 'Minimum input delay values in timing reports do not match delays in traces and part definitions.'


def check(oPortProfile):
    '''
    Purpose:  Check minimum input delay values match between configuration and timing reports.
    '''
    return port_delay_rules.check_minimum_delay(oPortProfile, port_delays.calculate_input_from_part_clock, port_delay_rules.INPUT_DELAY, RULE_ID, FAILURE_MESSAGE)
