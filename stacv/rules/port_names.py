'''
Compares a port named in a timing report with the port configured in the interface file.

A configured bus, written NAME[upper:lower], is reported one bit at a time, as NAME[bit].
'''

import re

BUS = r'(\w+)\[(\d+):(\d+)\]'
BIT = r'(\w+)\[(\d+)\]'


def matches_configured_port(sReportedPort, sConfiguredPort):
    oBus = re.fullmatch(BUS, sConfiguredPort)
    if oBus is None:
        return sReportedPort == sConfiguredPort
    return is_bit_of_bus(sReportedPort, oBus)


def is_bit_of_bus(sReportedPort, oBus):
    oBit = re.fullmatch(BIT, sReportedPort)
    if oBit is None:
        return False
    if oBit.group(1) != oBus.group(1):
        return False
    return is_within_bus_range(int(oBit.group(2)), int(oBus.group(2)), int(oBus.group(3)))


def is_within_bus_range(iBit, iUpper, iLower):
    return min(iUpper, iLower) <= iBit <= max(iUpper, iLower)
