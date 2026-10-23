'''
:Stage: 0 - inputs
:Applies to: SDR-SS-O, DDR-SS-O
:Reads: interface ports, trace delays, and part pins
:Depends on: none

The data trace and associated clock trace from the device to the part must exist.
This rule checks the trace and part TOML files for the existence of each trace.
If the traces do not exist then further analysis can not be performed.

**Likely causes**

* Traces do not exist in the trace TOML file
* Port definition in device interface is incorrect
* Pin definition in part TOML file is incorrect
'''

from stacv.results import rule_result
from stacv.rules import path_lookups


RULE_ID = 's0_trace_001'
FAILURE_MESSAGE = 'Data and/or clock trace does not exist.'


def check(oPortProfile):
    '''
    Purpose:  Checks the data and clock traces exist between the device and part.
    '''

    if not oPortProfile.traces.trace_starts_with_device_pin_named(oPortProfile.port.name):
        lDetail = [f'a trace does not start with the port {oPortProfile.port.name}']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    oDataTrace = path_lookups.get_data_trace(oPortProfile)
    if not oPortProfile.part.has_pin_named(oDataTrace.part_pin):
        lDetail = ['a part pin does not exist the data trace part pin does not exist on the part definition']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    oPartDataPin = path_lookups.get_part_data_pin(oPortProfile, oDataTrace)
    sPartClockPinName = oPartDataPin.clock.pin
    if not oPortProfile.traces.trace_ends_with_part_pin_named(sPartClockPinName):
        lDetail = [f'a clock trace does not exist for part pin {sPartClockPinName}']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    oDeviceClockPin = oPortProfile.port.capture_clock
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartDataPin, oDeviceClockPin)
    sDeviceClockPinName = oPortProfile.port.capture_clock.port
    if clock_trace_does_not_exist(oClockTrace, sDeviceClockPinName):
        lDetail = [f'a clock trace does not exist for device pin {sDeviceClockPinName}']
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, lDetail, FAILURE_MESSAGE)

    return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')


def clock_trace_does_not_exist(oClockTrace, sDeviceClockPinName):
    return oClockTrace is None or sDeviceClockPinName != oClockTrace.device_pin
