'''
Gives a part pin's setup, hold and clock to out, whichever form the part file gives them in.

An input pin gives a setup and a hold, or the window the clock edge must arrive in after its data changes.
An output pin gives a clock to out, or the window its data is valid in around the clock edge.
A window is converted with the interval between data changes: the clock period, or half of it for double data rate.
'''

from stacv.output import number_format


class PartTiming():
    '''
    A value of a part pin, with the calculation it comes from when it is converted from a window.
    '''

    def __init__(self, fValue, sName, lCalculation):
        self.value = fValue
        self.name = sName
        self.calculation = lCalculation


def calculate_data_change_interval(oPort):
    # The data changes once each period, or on both edges for double data rate.
    fPeriod = oPort.forwarded_clock.period
    if oPort.double_data_rate:
        return fPeriod / 2
    return fPeriod


def get_setup(oPin, oPort):
    if oPin.setup is not None:
        return PartTiming(oPin.setup.value, f'{oPin.name} setup', [])
    sCalculation = f'{oPin.name} setup = {oPin.skew_min.symbol} minimum = {format_time(oPin.skew_min.value)}'
    return PartTiming(oPin.skew_min.value, f'{oPin.name} setup', [sCalculation])


def get_hold(oPin, oPort):
    if oPin.hold is not None:
        return PartTiming(oPin.hold.value, f'{oPin.name} hold', [])
    fInterval = calculate_data_change_interval(oPort)
    fHold = fInterval - oPin.skew_max.value
    sCalculation = f'{oPin.name} hold = data change interval - {oPin.skew_max.symbol} maximum = {format_time(fInterval)} - {format_time(oPin.skew_max.value)} = {format_time(fHold)}'
    return PartTiming(fHold, f'{oPin.name} hold', [sCalculation])


def get_clock_to_out_max(oPin, oPort):
    if oPin.cko_max is not None:
        return PartTiming(oPin.cko_max.value, f'{oPin.name} clock to out maximum', [])
    fInterval = calculate_data_change_interval(oPort)
    fClockToOut = fInterval - oPin.valid_before.value
    sCalculation = f'{oPin.name} clock to out maximum = data change interval - {oPin.valid_before.symbol} = {format_time(fInterval)} - {format_time(oPin.valid_before.value)} = {format_time(fClockToOut)}'
    return PartTiming(fClockToOut, f'{oPin.name} clock to out maximum', [sCalculation])


def get_clock_to_out_min(oPin, oPort):
    if oPin.cko_min is not None:
        return PartTiming(oPin.cko_min.value, f'{oPin.name} clock to out minimum', [])
    sCalculation = f'{oPin.name} clock to out minimum = {oPin.valid_after.symbol} = {format_time(oPin.valid_after.value)}'
    return PartTiming(oPin.valid_after.value, f'{oPin.name} clock to out minimum', [sCalculation])


def format_time(fTime):
    return f'{number_format.format_number(fTime)} ns'
