'''
:Stage: 0 - inputs
:Applies to: all
:Reads: source or destination of every timing report, ``registers`` of the port in the configuration
:Depends on: none

Every register the port lists must start or end at least one path in its timing reports.
A listed register with no path is not timed: its name is wrong, or it does not drive or capture the port.
The rule passes when the port lists no registers.

**Result**

When the rule fails, it names each listed register no timing report has:

.. code-block:: text

     register q_mdio_out_reg of IO_MDIO is in no timing report

**Likely causes**

* The register's name in ``registers`` does not match its name in the netlist, such as a missing ``_reg``.
* Synthesis merged or removed the register.
'''

from stacv.results import rule_result
from stacv.rules import registers


RULE_ID = 's0_register_002'
FAILURE_MESSAGE = 'A register the port lists is in no timing report.'


def check(oPortProfile):
    '''
    Purpose:  Every register in the port's registers is in at least one timing report.
    '''
    oPort = oPortProfile.port
    lDetails = []
    if oPort.registers is not None:
        lReported = []
        for oTimingReport in oPortProfile.timing_reports.reports:
            lReported.append(registers.get_register(oTimingReport, oPort))
        for sPattern in oPort.registers:
            if not has_match(lReported, sPattern):
                lDetails.append(f'register {sPattern} of {oPort.name} is in no timing report')
    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def has_match(lRegisters, sPattern):
    for sRegister in lRegisters:
        if registers.matches(sRegister, sPattern):
            return True
    return False
