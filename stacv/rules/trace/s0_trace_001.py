'''
:Stage: 0 - Input Checks
:Applies to: SDR-SS-O, DDR-SS-O
:Reads: interface, trace delays, and part setup value
:Depends on: none

The data trace and associated clock trace from the device to the part must exist.
This rule checks the trace and part TOML files for the existence of each trace.
If the traces do not exist then further analysis can be performed.

**Likely causes**

* Traces do not exist in the trace TOML file
* Port definition in device interface is incorrect
* Pin definition in part TOML file is incorrect
'''

from stacv.results import rule_result
from stacv.rules import path_lookups


RULE_ID = 's0_trace_001'


def check(oPortProfile):
    '''
    Purpose:  Checks the data and clock traces exist between the device and port.
    '''

    if not oPortProfile.traces.trace_starts_with_device_pin_named(oPortProfile.port.name):
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, [], f'the data trace does not start with the port {oPortProfile.port.name}')

    oDataTrace = oPortProfile.traces.get_device_to_part_trace_starting_with_name(oPortProfile.port.name)
    if not oPortProfile.part.has_pin_named(oDataTrace.part_pin):
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, [], f'the data trace part pin does not exist on the part definition')

    oPartDataPin = oPortProfile.part.get_pin_named(oDataTrace.part_pin)
    sPartClockPinName = oPartDataPin.clock.pin
    if not oPortProfile.traces.trace_ends_with_part_pin_named(sPartClockPinName):
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, [], f'a clock trace does not exist for part pin {sPartClockPinName}')

    oClockTrace = oPortProfile.traces.get_device_to_part_trace_ending_with_name(sPartClockPinName)
    sDeviceClockPinName = oPortProfile.port.capture_clock.port
    if sDeviceClockPinName != oClockTrace.device_pin:        
        return rule_result.RuleResult(RULE_ID, rule_result.FAILED, [], f'a clock trace does not exist for device pin {sDeviceClockPinName}')

    return rule_result.RuleResult(RULE_ID, rule_result.PASSED, [], '')
