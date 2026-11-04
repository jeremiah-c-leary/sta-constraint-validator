'''
Changes to the VSC8540ET example files that the rule tests make.
'''


def build_trace(sName, sDevicePin, sPartPin, sDirection, fMaxDelay, fMinDelay):
    return f'name = "{sName}"\ndevice_pin = "{sDevicePin}"\npart_pin = "{sPartPin}"\n{sDirection} = {{max_delay = {fMaxDelay}, min_delay = {fMinDelay}}}'


def lengthen_trace(sName, sDevicePin, sPartPin, sDirection):
    # Every example data trace is 0.8 ns to 1.2 ns; one nanosecond longer moves each delay by 1 ns.
    return (build_trace(sName, sDevicePin, sPartPin, sDirection, 1.2, 0.8), build_trace(sName, sDevicePin, sPartPin, sDirection, 2.2, 1.8))
