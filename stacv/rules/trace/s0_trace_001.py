'''
:Stage: 0 - inputs
:Applies to: SDR-SS-O, SDR-SS-RT-DI, DDR-SS-O
:Reads: interface ports, trace delays, and part pins
:Depends on: none

The data trace and associated clock trace must exist.
The data trace runs from the device to the part for an output, and from the part to the device for an SDR-SS-RT-DI port.
The clock trace runs from the device's clock port to the clock pin of the part pin.
This rule checks the trace and part TOML files for the existence of each trace.
If the traces do not exist then further analysis can not be performed.

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
    sPartClockPinName = oPartDataPin.clock.pin
    if not oPortProfile.traces.trace_ends_with_part_pin_named(sPartClockPinName):
        lDetail = [f'a clock trace does not exist for part pin {sPartClockPinName}']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartDataPin)
    sDeviceClockPinName = oPortProfile.port.forwarded_clock.port
    if clock_trace_does_not_exist(oClockTrace, sDeviceClockPinName):
        lDetail = [f'a clock trace does not exist for device pin {sDeviceClockPinName}']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')


def describe_trace_end(oPort):
    # An output's trace starts at the port, and an input's trace ends at it.
    if oPort.data_direction == methodology.INPUT:
        return 'end with'
    return 'start with'


def clock_trace_does_not_exist(oClockTrace, sDeviceClockPinName):
    return oClockTrace is None
