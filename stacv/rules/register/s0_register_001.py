'''
:Stage: 0 - inputs
:Applies to: all
:Reads: source or destination of every timing report, ``registers`` of the port in the configuration
:Depends on: none

Every path in the timing reports of a port must start at, or end at, a register the port lists.
An output port's paths start at the registers that drive it, and an input port's paths end at the registers that capture it.
The report script reports every path to or from the port, not only the worst, so a register that is not listed shows up here.
A register that is not listed means the configuration does not say everything the port times: logic before the pin, or an extra flop capturing the data.

A register in ``registers`` can use ``*`` for any characters, such as ``q_txd_reg[*]`` for every bit of a bus.

**Result**

When the rule fails, it lists each timing report whose register is not listed, with the file and line of the report's slack:

.. code-block:: text

     IO_MDIO_write_timing.rpt:14  register q_mdio_oe_reg is not in registers of IO_MDIO

**Likely causes**

* A register that drives or captures the port is missing from ``registers``.
* The design has logic, or an extra register, between the port and the register the user expected.
'''

from stacv.results import rule_result
from stacv.rules import registers
from stacv.rules import rule_details


RULE_ID = 's0_register_001'
FAILURE_MESSAGE = 'A timing path starts or ends at a register the port does not list.'


def check(oPortProfile):
    '''
    Purpose:  Every register in the timing reports is listed in the port's registers.
    '''
    oPort = oPortProfile.port
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        sRegister = registers.get_register(oTimingReport, oPort)
        if not registers.is_listed(sRegister, oPort.registers):
            lDetails.append(rule_details.format_detail(oTimingReport.slack_line, f'register {sRegister} is not in registers of {oPort.name}'))
    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)
