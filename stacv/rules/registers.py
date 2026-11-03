'''
Finds the register at the device end of a timing path, and matches it against the port's registers.

An output port's paths start at the register that drives the port: the cell of the timing report's source.
An input port's paths end at the register that captures it: the cell of the timing report's destination.
A register in the interface file can use * for any characters, such as q_txd_reg[*] for every bit of a bus.
'''

import re


from stacv.methodology import methodology

# The most paths the report script asks for in one report; a report with this many may have left paths out.
PATH_LIMIT = 100


def get_register(oTimingReport, oPort):
    if oPort.data_direction == methodology.INPUT:
        return remove_pin(oTimingReport.destination)
    return remove_pin(oTimingReport.source)


def remove_pin(sCellPin):
    # A source or destination is written cell/pin, such as q_mdio_out_reg/C.
    return sCellPin.rsplit('/', 1)[0]


def is_listed(sRegister, lRegisters):
    for sPattern in lRegisters:
        if matches(sRegister, sPattern):
            return True
    return False


def matches(sRegister, sPattern):
    lParts = []
    for sPart in sPattern.split('*'):
        lParts.append(re.escape(sPart))
    return re.fullmatch('.*'.join(lParts), sRegister) is not None


def group_reports_by_register(lReports, oPort):
    # Each register's reports, in the order the registers first appear.
    lGroups = []
    dGroups = {}
    for oTimingReport in lReports:
        sRegister = get_register(oTimingReport, oPort)
        if sRegister not in dGroups:
            dGroups[sRegister] = []
            lGroups.append(dGroups[sRegister])
        dGroups[sRegister].append(oTimingReport)
    return lGroups
