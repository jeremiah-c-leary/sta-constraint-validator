
from stacv.config import config_reader
from stacv.config import value_type

from stacv.part import clock_pin
from stacv.part import constraint
from stacv.part import datasheet
from stacv.part import interface
from stacv.part import interface_list
from stacv.part import part_config_error
from stacv.part import part_location
from stacv.part import pin
from stacv.part import pin_list

READER = config_reader.ConfigReader('part_config', part_config_error.PartConfigError)
TOP_LEVEL_KEYS = ['properties', 'datasheet', 'interface']
PROPERTIES_KEYS = ['manufacturer', 'part_number']
DATASHEET_KEYS = ['name', 'url', 'version']
INTERFACE_KEYS = ['name', 'pin']
PIN_KEYS = ['name', 'methodology', 'clock']
CLOCK_KEYS = ['pin', 'max_frequency', 'duty_cycle']
DUTY_CYCLE_KEYS = ['min', 'max']
CONSTRAINT_KEYS = ['value', 'symbol', 'source']
EDGES = ['Rising', 'Falling', 'Both']


class Part():

    def __init__(self):
        self.manufacturer = None
        self.part_number = None
        self.datasheet = None
        self.interfaces = None
        # The name of the part interface the interface file uses, or None to look at every interface.
        self.selected_interface = None

    def get_pin_named(self, sPinName, sMethodology=None):
        # The interface file can name the part interface it uses; its pins are then the only ones looked at.
        return self.interfaces.get_pin_named(sPinName, sMethodology, self.selected_interface)

    def has_pin_named(self, sPinName, sMethodology=None):
        return self.get_pin_named(sPinName, sMethodology) is not None

    def has_interface_named(self, sInterfaceName):
        return self.interfaces.get_interface_named(sInterfaceName) is not None


def create_part(oInterface):
    dPart = READER.read_toml_file(oInterface.part)
    oPart = build_part(dPart, oInterface.part)
    select_part_interface(oPart, oInterface)
    return oPart


def select_part_interface(oPart, oInterface):
    if oInterface.part_interface is None:
        return
    if not oPart.has_interface_named(oInterface.part_interface):
        READER.raise_error(9, oInterface.part, f'has no interface named {oInterface.part_interface}, which key "part_interface" of the interface file names')
    oPart.selected_interface = oInterface.part_interface


def build_part(dPart, sFilename):
    oLocation = part_location.PartLocation(sFilename)
    READER.check_keys(dPart, TOP_LEVEL_KEYS, oLocation)
    oPart = Part()
    oPropertiesLocation = table_location(sFilename, 'properties')
    dProperties = read_table(dPart, 'properties', PROPERTIES_KEYS, sFilename)
    oPart.manufacturer = READER.get_required_string(dProperties, 'manufacturer', oPropertiesLocation)
    oPart.part_number = READER.get_required_string(dProperties, 'part_number', oPropertiesLocation)
    oPart.datasheet = build_datasheet(read_table(dPart, 'datasheet', DATASHEET_KEYS, sFilename), table_location(sFilename, 'datasheet'))
    oPart.interfaces = build_interface_list(READER.get_required_array_of_tables(dPart, 'interface', oLocation), sFilename)
    return oPart


def read_table(dPart, sTable, lKeys, sFilename):
    dTable = READER.get_required_table(dPart, sTable, part_location.PartLocation(sFilename))
    READER.check_keys(dTable, lKeys, table_location(sFilename, sTable))
    return dTable


def table_location(sFilename, sTable):
    oLocation = part_location.PartLocation(sFilename)
    oLocation.set_table(sTable)
    return oLocation


def build_datasheet(dDatasheet, oLocation):
    oDatasheet = datasheet.Datasheet()
    oDatasheet.name = READER.get_required_string(dDatasheet, 'name', oLocation)
    oDatasheet.url = READER.get_required_string(dDatasheet, 'url', oLocation)
    oDatasheet.version = READER.get_required_string(dDatasheet, 'version', oLocation)
    return oDatasheet


def build_interface_list(lInterfaces, sFilename):
    oInterfaceList = interface_list.InterfaceList()
    oInterfaceList.interfaces = []
    for iInterface, dInterface in enumerate(lInterfaces, start=1):
        oInterfaceList.interfaces.append(build_interface(dInterface, iInterface, sFilename))
    check_pins_are_defined_once(oInterfaceList, sFilename)
    return oInterfaceList


def check_pins_are_defined_once(oInterfaceList, sFilename):
    # Modes of a part share pin names, so a pin is identified by its interface, its name and its methodology:
    # a bidirectional pin, such as MDIO, has one table for each direction.
    for oInterface in oInterfaceList.interfaces:
        lKeys = []
        for oPin in oInterface.pins.pins:
            sKey = oPin.name + '.' + oPin.methodology
            if sKey in lKeys:
                READER.raise_error(7, sFilename, f'pin {oPin.name} with methodology {oPin.methodology} is defined by more than one [[interface.pin]] table in interface {oInterface.name}')
            lKeys.append(sKey)


def build_interface(dInterface, iInterface, sFilename):
    oLocation = part_location.PartLocation(sFilename)
    oLocation.set_interface_number(iInterface)
    if has_valid_name(dInterface):
        oLocation.set_interface_name(dInterface['name'])
    READER.check_keys(dInterface, INTERFACE_KEYS, oLocation)
    oInterface = interface.Interface()
    oInterface.name = READER.get_required_string(dInterface, 'name', oLocation)
    oInterface.pins = build_pin_list(READER.get_required_array_of_tables(dInterface, 'pin', oLocation), oInterface.name, sFilename)
    return oInterface


def has_valid_name(dTable):
    # A table is named by its name only once the name is valid; until then it is named by its number.
    return 'name' in dTable and value_type.STRING.is_valid(dTable['name'])


def build_pin_list(lPins, sInterfaceName, sFilename):
    oPinList = pin_list.PinList()
    oPinList.pins = []
    for iPin, dPin in enumerate(lPins, start=1):
        oPinList.pins.append(build_pin(dPin, iPin, sInterfaceName, sFilename))
    return oPinList


def build_pin(dPin, iPin, sInterfaceName, sFilename):
    oLocation = part_location.PartLocation(sFilename)
    oLocation.set_pin_number(iPin, sInterfaceName)
    if has_valid_name(dPin):
        oLocation.set_pin_name(dPin['name'], sInterfaceName)
    # The methodology decides the keys a pin has, so it is read before the keys are checked.
    sMethodology = READER.get_required_string(dPin, 'methodology', oLocation)
    oPinType = find_pin_type(sMethodology, oLocation)
    READER.check_keys(dPin, PIN_KEYS + oPinType.keys, oLocation)
    oPin = pin.Pin()
    oPin.name = READER.get_required_string(dPin, 'name', oLocation)
    oLocation.set_pin_name(oPin.name, sInterfaceName)
    oPin.methodology = sMethodology
    oPin.clock = build_clock_pin(dPin, oPin.name, sInterfaceName, oLocation)
    oPinType.build(oPin, dPin, sInterfaceName, oLocation)
    return oPin


def find_pin_type(sMethodology, oLocation):
    if sMethodology not in PIN_TYPES:
        READER.raise_error(5, oLocation.filename, f'key "methodology"{oLocation.location} names {sMethodology}; a part pin is {describe_pin_methodologies()}')
    return PIN_TYPES[sMethodology]


def describe_pin_methodologies():
    lNames = list(PIN_TYPES)
    return ', '.join(lNames[:-1]) + ' or ' + lNames[-1]


def read_pin_table(dPin, sTable, lKeys, oPinLocation, oTableLocation):
    dTable = READER.get_required_table(dPin, sTable, oPinLocation)
    READER.check_keys(dTable, lKeys, oTableLocation)
    return dTable


def pin_table_location(sTable, sPinName, sInterfaceName, sFilename):
    oLocation = part_location.PartLocation(sFilename)
    oLocation.set_pin_table(sTable, sPinName, sInterfaceName)
    return oLocation


def build_clock_pin(dPin, sPinName, sInterfaceName, oPinLocation):
    oLocation = pin_table_location('clock', sPinName, sInterfaceName, oPinLocation.filename)
    dClock = read_pin_table(dPin, 'clock', CLOCK_KEYS, oPinLocation, oLocation)
    oClockPin = clock_pin.ClockPin()
    oClockPin.pin = READER.get_required_string(dClock, 'pin', oLocation)
    oClockPin.max_frequency = READER.get_required_number(dClock, 'max_frequency', oLocation)
    if oClockPin.max_frequency <= 0:
        READER.raise_error(8, oLocation.filename, f'key "max_frequency"{oLocation.location} must be greater than 0')
    if 'duty_cycle' in dClock:
        dDutyCycle = READER.get_required_table(dClock, 'duty_cycle', oLocation)
        READER.check_keys(dDutyCycle, DUTY_CYCLE_KEYS, oLocation)
        oClockPin.duty_cycle_min = READER.get_required_number(dDutyCycle, 'min', oLocation)
        oClockPin.duty_cycle_max = READER.get_required_number(dDutyCycle, 'max', oLocation)
    return oClockPin


def build_constraint(dPin, sTable, sPinName, sInterfaceName, oPinLocation):
    oLocation = pin_table_location(sTable, sPinName, sInterfaceName, oPinLocation.filename)
    dConstraint = read_pin_table(dPin, sTable, CONSTRAINT_KEYS, oPinLocation, oLocation)
    oConstraint = constraint.Constraint()
    oConstraint.value = READER.get_required_number(dConstraint, 'value', oLocation)
    oConstraint.symbol = READER.get_required_string(dConstraint, 'symbol', oLocation)
    oConstraint.source = READER.get_required_string(dConstraint, 'source', oLocation)
    return oConstraint


def read_edge(dPin, sKey, oLocation):
    sEdge = READER.get_required_string(dPin, sKey, oLocation)
    if sEdge not in EDGES:
        READER.raise_error(6, oLocation.filename, f'key "{sKey}"{oLocation.location} must be "{EDGES[0]}", "{EDGES[1]}" or "{EDGES[2]}"')
    return sEdge


def build_input_pin(oPin, dPin, sInterfaceName, oLocation):
    oPin.capture_edge = read_edge(dPin, 'capture_edge', oLocation)
    oPin.setup = build_constraint(dPin, 'setup', oPin.name, sInterfaceName, oLocation)
    oPin.hold = build_constraint(dPin, 'hold', oPin.name, sInterfaceName, oLocation)


def build_output_pin(oPin, dPin, sInterfaceName, oLocation):
    # An output is given as a clock to out, or as the window its data is valid in around the clock edge.
    oPin.launch_edge = read_edge(dPin, 'launch_edge', oLocation)
    if read_timing_form(dPin, ['cko_max', 'cko_min'], ['valid_before', 'valid_after'], oLocation) == 0:
        oPin.cko_max = build_constraint(dPin, 'cko_max', oPin.name, sInterfaceName, oLocation)
        oPin.cko_min = build_constraint(dPin, 'cko_min', oPin.name, sInterfaceName, oLocation)
    else:
        oPin.valid_before = build_constraint(dPin, 'valid_before', oPin.name, sInterfaceName, oLocation)
        oPin.valid_after = build_constraint(dPin, 'valid_after', oPin.name, sInterfaceName, oLocation)


def read_timing_form(dPin, lFirstForm, lSecondForm, oLocation):
    # Exactly one form gives the pin's timing: 0 for the first form, 1 for the second.
    bFirstForm = has_any_key(dPin, lFirstForm)
    bSecondForm = has_any_key(dPin, lSecondForm)
    if bFirstForm == bSecondForm:
        READER.raise_error(10, oLocation.filename, f'timing{oLocation.location} must give {" and ".join(lFirstForm)}, or {" and ".join(lSecondForm)}')
    if bFirstForm:
        return 0
    return 1


def has_any_key(dTable, lKeys):
    for sKey in lKeys:
        if sKey in dTable:
            return True
    return False


class PinType():
    '''
    The keys a part pin of one methodology has, beyond the keys every pin has, and how they are read.
    '''

    def __init__(self, lKeys, fBuild):
        self.keys = lKeys
        self.build = fBuild


INPUT_PIN = PinType(['capture_edge', 'setup', 'hold'], build_input_pin)
OUTPUT_PIN = PinType(['launch_edge', 'cko_max', 'cko_min', 'valid_before', 'valid_after'], build_output_pin)

# Part pin methodologies are named from the part's view.
PIN_TYPES = {}
PIN_TYPES['SDR-SS-I'] = INPUT_PIN
PIN_TYPES['SDR-SS-O'] = OUTPUT_PIN
# An output timed to the first and last edges of a clock that stops, such as a chip select from the device's datasheet:
# valid_before is before the first edge and valid_after after the last.
PIN_TYPES['SDR-SS-O-FLC'] = OUTPUT_PIN
PIN_TYPES['SDR-SS-RT-DI'] = INPUT_PIN
PIN_TYPES['SDR-SS-RT-DO'] = OUTPUT_PIN
PIN_TYPES['SDR-SYS-I'] = INPUT_PIN
PIN_TYPES['SDR-SYS-O'] = OUTPUT_PIN
PIN_TYPES['DDR-SS-I'] = INPUT_PIN
PIN_TYPES['DDR-SS-O'] = OUTPUT_PIN


def is_input_pin(oPin):
    return PIN_TYPES[oPin.methodology] is INPUT_PIN
