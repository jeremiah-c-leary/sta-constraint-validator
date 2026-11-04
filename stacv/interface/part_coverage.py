'''
Checks every pin of the part interface the interface file uses has a port in the interface file.

A pin is connected to a device port by a trace, and the port times it when the port's methodology is the pin's,
seen from the device.  A deferred port also covers a pin: the pin is not timed yet, but it is listed, so the
user has seen it.  A pin with no port could be left out of the timing without anyone noticing.
'''

from stacv.interface import interface_config_error
from stacv.interface import port
from stacv.methodology import methodology_factory
from stacv.part import part
from stacv.traces import traces_config_error


def check_every_part_pin_has_a_port(sInterfaceFile, oInterface, oTraceList, oPart):
    oPartInterface = oPart.interfaces.get_interface_named(oPart.selected_interface)
    if oPartInterface is None:
        return
    for oPin in oPartInterface.pins.pins:
        check_pin_has_a_port(sInterfaceFile, oInterface, oTraceList, oPin, oPartInterface.name)


def check_pin_has_a_port(sInterfaceFile, oInterface, oTraceList, oPin, sPartInterfaceName):
    sPin = describe_pin(oPin, sPartInterfaceName)
    lDevicePins = find_device_pins_of_traces_to_pin(oTraceList, oPin)
    if len(lDevicePins) == 0:
        raise traces_config_error.TracesConfigError('traces_config_010', oInterface.traces, f'{sPin} has no trace to a device port; add a trace for it, and a [[port]] or a deferred port in the interface file')
    for sDevicePin in lDevicePins:
        if has_port_for_pin(oInterface, sDevicePin, oPin):
            return
    raise interface_config_error.InterfaceConfigError('interface_config_024', sInterfaceFile, f'{sPin} has no port; add a [[port]] for it, named {" or ".join(lDevicePins)} after its trace, or a deferred one')


def describe_pin(oPin, sPartInterfaceName):
    # A bidirectional pin is listed once for each methodology, so the methodology names which one.
    return f'pin {oPin.name} ({oPin.methodology}) of part interface {sPartInterfaceName}'


def find_device_pins_of_traces_to_pin(oTraceList, oPin):
    # A traces file can be shared by the interfaces of a part with several modes, so a pin can have a trace for each.
    # The part captures on an input pin, so its data comes from the device; an output pin's data goes to the device.
    if part.PIN_TYPES[oPin.methodology] == part.INPUT_PIN:
        lTraces = oTraceList.get_device_to_part_traces()
    else:
        lTraces = oTraceList.get_part_to_device_traces()
    lDevicePins = []
    for oTrace in lTraces:
        if oTrace.part_pin == oPin.name:
            lDevicePins.append(oTrace.device_pin)
    return lDevicePins


def has_port_for_pin(oInterface, sPortName, oPin):
    for oPort in oInterface.ports:
        if oPort.name == sPortName and port_covers_pin(oPort, oPin):
            return True
    return False


def port_covers_pin(oPort, oPin):
    # A deferred port's methodology is not checked, so it covers the pin unless it names one that is not the pin's.
    if oPort.status == port.DEFER:
        return deferred_port_covers_pin(oPort, oPin)
    return oPort.part_pin_methodology == oPin.methodology


def deferred_port_covers_pin(oPort, oPin):
    oMethodology = methodology_factory.create_methodology(oPort.methodology)
    if oMethodology is None:
        return True
    return oMethodology.part_pin_methodology == oPin.methodology
