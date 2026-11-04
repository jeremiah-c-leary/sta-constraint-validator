'''
:Stage: 0 - inputs
:Applies to: all
:Reads: interface ports, trace delays, and part pins
:Depends on: none

The data trace and associated clock trace must exist.
The data trace runs from the device to the part for an output, and from the part to the device for an input.
The clock trace depends on where the clock comes from:

* the device: a trace from the device's clock port to the clock pin of the part pin
* the part: a trace from the clock pin of the part pin to the device's clock port
* a clock source: a trace from the source to the device's clock port, and a trace from the same source to the clock pin of the part pin

This rule checks the trace and part TOML files for the existence of each trace.
If the traces do not exist then further analysis can not be performed.

Every pin of the part interface must have a trace and a port before any rule runs (traces_config_010 and interface_config_024),
so a missing or miswired data trace is usually reported by those errors first.
The rule still finds a data trace problem when the part pin has a trace to another port, and it checks the clock traces, which those errors do not.

**Likely causes**

* Traces do not exist in the trace TOML file
* Port definition in device interface is incorrect
* Pin definition in part TOML file is incorrect
'''

from stacv.methodology import methodology
from stacv.results import rule_result
from stacv.rules import path_lookups


RULE_ID = 's0_trace_001'
FAILURE_MESSAGE = 'Data and/or clock trace does not exist.'


def check(oPortProfile):
    '''
    Purpose:  Checks the data and clock traces exist between the device and part.
    '''

    oDataTrace = path_lookups.get_port_data_trace(oPortProfile)
    if oDataTrace is None:
        lDetail = [f'a trace does not {describe_trace_end(oPortProfile.port)} the port {oPortProfile.port.name}']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    if not oPortProfile.part.has_pin_named(oDataTrace.part_pin):
        lDetail = [f'the data trace does not connect to pin {oDataTrace.part_pin} on the part']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    oPartDataPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    lDetail = find_missing_clock_trace(oPortProfile, oPartDataPin)
    if len(lDetail) > 0:
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')


def find_missing_clock_trace(oPortProfile, oPartDataPin):
    if oPortProfile.port.clock_origin == methodology.PART_CLOCK:
        return find_missing_part_clock_trace(oPortProfile, oPartDataPin)
    if oPortProfile.port.clock_origin == methodology.SOURCE_CLOCK:
        return find_missing_source_clock_traces(oPortProfile, oPartDataPin)
    return find_missing_device_clock_trace(oPortProfile, oPartDataPin)


def find_missing_device_clock_trace(oPortProfile, oPartDataPin):
    sPartClockPinName = oPartDataPin.clock.pin
    if not oPortProfile.traces.trace_ends_with_part_pin_named(sPartClockPinName):
        return [f'a clock trace does not exist for part pin {sPartClockPinName}']
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartDataPin)
    if oClockTrace is None:
        return [f'a clock trace does not exist for device pin {oPortProfile.port.forwarded_clock.port}']
    return []


def find_missing_part_clock_trace(oPortProfile, oPartDataPin):
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartDataPin)
    if oClockTrace is None:
        return [f'a clock trace does not run from part pin {oPartDataPin.clock.pin} to device pin {oPortProfile.port.forwarded_clock.port}']
    return []


def find_missing_source_clock_traces(oPortProfile, oPartDataPin):
    sDeviceClockPinName = oPortProfile.port.forwarded_clock.port
    if path_lookups.get_source_to_device_clock_trace(oPortProfile) is None:
        return [f'a clock trace does not run from a clock source to device pin {sDeviceClockPinName}']
    if path_lookups.get_source_to_part_clock_trace(oPortProfile, oPartDataPin) is None:
        return [f'a clock trace does not run from the clock source of device pin {sDeviceClockPinName} to part pin {oPartDataPin.clock.pin}']
    return []


def describe_trace_end(oPort):
    # An output's trace starts at the port, and an input's trace ends at it.
    if oPort.data_direction == methodology.INPUT:
        return 'end with'
    return 'start with'
