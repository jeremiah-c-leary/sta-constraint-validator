
import tomllib

from stacv.part import clock_pin
from stacv.part import constraint
from stacv.part import datasheet
from stacv.part import interface
from stacv.part import interface_list
from stacv.part import pin
from stacv.part import pin_list


class Part():

    def __init__(self):
        self.manufacturer = None
        self.part_number = None
        self.datasheet = None
        self.interfaces = None

    def get_pin_named(self, sPinName):
        return self.interfaces.get_pin_named(sPinName)


def create_part(oInterface):
    dPart = read_toml_file(oInterface.part)
    return build_part(dPart)


def read_toml_file(sFilename):
    with open(sFilename, 'rb') as oFile:
        return tomllib.load(oFile)


def build_part(dPart):
    oPart = Part()
    oPart.manufacturer = dPart['properties']['manufacturer']
    oPart.part_number = dPart['properties']['part_number']
    oPart.datasheet = build_datasheet(dPart['datasheet'])
    oPart.interfaces = build_interface_list(dPart['interface'])
    return oPart


def build_interface_list(dInterfaces):
    oInterfaceList = interface_list.InterfaceList()
    oInterfaceList.interfaces = build_interfaces(dInterfaces)
    return oInterfaceList


def build_interfaces(dInterfaces):
    lInterfaces = []
    for dInterface in dInterfaces:
        oInterface = build_interface(dInterface)
        lInterfaces.append(oInterface)
    return lInterfaces


def build_interface(dInterface):
    oInterface = interface.Interface()
    oInterface.name = dInterface['name']
    oInterface.pins = build_pin_list(dInterface['pin'])
    return oInterface


def build_pin_list(dPins):
    oPinList = pin_list.PinList()
    oPinList.pins = build_pins(dPins)
    return oPinList


def build_pins(dPins):
    lPins = []
    for dPin in dPins:
        oPin = create_pin(dPin)
        lPins.append(oPin)
    return lPins


def create_pin(dPin):
    return dPinMap[dPin['methodology']](dPin)


def build_datasheet(dDatasheet):
    oDatasheet = datasheet.Datasheet()
    oDatasheet.name = dDatasheet['name']
    oDatasheet.url = dDatasheet['url']
    oDatasheet.version = dDatasheet['version']
    return oDatasheet


def build_sdr_ss_i_pin(dPin):
    oPin = build_base_pin(dPin)
    oPin.capture_edge = dPin['capture_edge']
    oPin.setup = build_constraint(dPin['setup'])
    oPin.hold = build_constraint(dPin['hold'])
    return oPin


def build_base_pin(dPin):
    oPin = pin.Pin()
    oPin.name = dPin['name']
    oPin.methodology = dPin['methodology']
    oPin.clock = build_clock_pin(dPin['clock'])
    return oPin


def build_clock_pin(dClock):
    oClockPin = clock_pin.ClockPin()
    oClockPin.pin = dClock['pin']
    oClockPin.max_frequency = dClock['max_frequency']
    return oClockPin


def build_constraint(dConstraint):
    oConstraint = constraint.Constraint()
    oConstraint.value = dConstraint['value']
    oConstraint.symbol = dConstraint['symbol']
    oConstraint.source = dConstraint['source']
    return oConstraint


def build_sdr_ss_o_pin(dPin):
    oPin = build_base_pin(dPin)
    oPin.launch_edge = dPin['launch_edge']
    oPin.cko_max = build_constraint(dPin['cko_max'])
    oPin.cko_min = build_constraint(dPin['cko_min'])


dPinMap = {}
dPinMap['SDR-SS-I'] = build_sdr_ss_i_pin
dPinMap['SDR-SS-O'] = build_sdr_ss_o_pin

