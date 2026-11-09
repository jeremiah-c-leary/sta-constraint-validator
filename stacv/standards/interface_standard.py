'''
Links the interface, part and traces files by the signals of the interface standard they follow, and checks the
interface against the standard.

Each trace that names an if_signal runs from the port, or the clock's port, with that signal to the part pin with that
signal, so its device_pin and part_pin are filled in here, and every command after this works on pin names as before.

The checks:

    the standard, the role and each signal are ones the standard has
    each signal is carried once in each file; the clocks of one port may share a signal
    the part interface follows the same standard, in the other role
    every signal of the standard has a port or clock, a part pin and a trace
    each signal goes the way its driver sends it: out of the device when the device drives it
    each signal changes and is sampled on the edges of the standard's mode, and the clock idles at its level
'''

from stacv.methodology import methodology
from stacv.part import part
from stacv.standards import standard_error
from stacv.standards import standards


def link_and_check(sInterfaceFile, oInterface, oTraceList, oPart):
    oPartInterface = oPart.interfaces.get_interface_named(oPart.selected_interface)
    if oInterface.if_standard is None:
        check_no_signals_without_standard(sInterfaceFile, oInterface, oTraceList)
        return
    oStandard = read_standard(oInterface.if_standard, sInterfaceFile)
    check_role(oStandard, oInterface.if_role, sInterfaceFile, 'the interface file')
    check_part_interface(oStandard, oInterface, oPartInterface)
    check_interface_signals(oStandard, sInterfaceFile, oInterface)
    check_part_signals(oStandard, oInterface, oPartInterface)
    check_trace_signals(oStandard, oInterface, oTraceList)
    link_traces(sInterfaceFile, oInterface, oTraceList, oPartInterface)
    check_directions(oStandard, sInterfaceFile, oInterface, oTraceList, oPartInterface)
    check_edges(oStandard, sInterfaceFile, oInterface, oPartInterface)


def raise_error(iNumber, sFilename, sMessage):
    raise standard_error.StandardError(f'if_standard_{iNumber:03d}', sFilename, sMessage)


def check_no_signals_without_standard(sInterfaceFile, oInterface, oTraceList):
    # A signal only means something in a standard, so a file that names none cannot use them.
    for sDescription, sSignal in collect_interface_signals(oInterface):
        raise_error(1, sInterfaceFile, f'{sDescription} gives if_signal {sSignal}, but the interface file names no if_standard')
    for oTrace in oTraceList.traces:
        if oTrace.if_signal is not None:
            raise_error(1, oInterface.traces, f'trace {oTrace.name} gives if_signal {oTrace.if_signal}, but the interface file names no if_standard')


def read_standard(sName, sFilename):
    oStandard = standards.get_standard(sName)
    if oStandard is None:
        raise_error(2, sFilename, f'key "if_standard" names {sName}; the standards are {join_names(standards.get_standard_names())}')
    return oStandard


def check_role(oStandard, sRole, sFilename, sDescription):
    if sRole is None:
        raise_error(3, sFilename, f'{sDescription} names if_standard {oStandard.name} but no if_role; give if_role {join_names(oStandard.roles)}')
    if sRole not in oStandard.roles:
        raise_error(3, sFilename, f'key "if_role" names {sRole}; the roles of {oStandard.name} are {join_names(oStandard.roles)}')


def check_part_interface(oStandard, oInterface, oPartInterface):
    # The part is the other side of the same interface.
    sDescription = f'part interface {oPartInterface.name}'
    if oPartInterface.if_standard is None:
        raise_error(6, oInterface.part, f'{sDescription} names no if_standard; the interface file follows {oStandard.name}')
    if oPartInterface.if_standard != oStandard.name:
        raise_error(6, oInterface.part, f'{sDescription} follows {oPartInterface.if_standard}, but the interface file follows {oStandard.name}')
    check_role(oStandard, oPartInterface.if_role, oInterface.part, sDescription)
    if oPartInterface.if_role == oInterface.if_role:
        raise_error(6, oInterface.part, f'{sDescription} is the {oPartInterface.if_role}, as is the device; the part must be the {oStandard.get_other_role(oInterface.if_role)}')


def check_signal_name(oStandard, sSignal, sFilename, sDescription):
    # A signal that repeats is numbered, CS.1; any other signal is not.
    oSignal = oStandard.get_signal(sSignal)
    if oSignal is None:
        raise_error(4, sFilename, f'{sDescription} gives if_signal {sSignal}, which is not a signal of {oStandard.name}; the signals are {join_names(oStandard.get_signal_names())}')
    bNumbered = standards.SIGNAL_NUMBER_SEPARATOR in sSignal
    if bNumbered and not oSignal.repeats:
        raise_error(4, sFilename, f'{sDescription} gives if_signal {sSignal}, but {oSignal.name} does not repeat, so it is not numbered')
    if bNumbered and not sSignal.split(standards.SIGNAL_NUMBER_SEPARATOR)[1].isdigit():
        raise_error(4, sFilename, f'{sDescription} gives if_signal {sSignal}; a repeated signal is numbered {oSignal.name}.1, {oSignal.name}.2, ...')
    return oSignal


def collect_interface_signals(oInterface):
    # Each clock and port that gives a signal, described for messages.
    lSignals = []
    for oClock in oInterface.clocks:
        if oClock.if_signal is not None:
            lSignals.append((f'clock {oClock.name}', oClock.if_signal))
    for oPort in oInterface.ports:
        if oPort.if_signal is not None:
            lSignals.append((f'port {oPort.name}', oPort.if_signal))
    return lSignals


def check_interface_signals(oStandard, sInterfaceFile, oInterface):
    for sDescription, sSignal in collect_interface_signals(oInterface):
        check_signal_name(oStandard, sSignal, sInterfaceFile, sDescription)
    for oClock in oInterface.clocks:
        if oClock.if_signal is not None and oClock.port is None:
            raise_error(7, sInterfaceFile, f'clock {oClock.name} gives if_signal {oClock.if_signal} but no port; a signal crosses the board at a port')
    dCarriers = {}
    for sDescription, sSignal, sDevicePin in collect_device_pins(oInterface):
        if sSignal in dCarriers and not can_share_signal(dCarriers[sSignal], (sDescription, sDevicePin)):
            raise_error(5, sInterfaceFile, f'{dCarriers[sSignal][0]} and {sDescription} both give if_signal {sSignal}; a signal is carried by one port, or by clocks of one port')
        dCarriers[sSignal] = (sDescription, sDevicePin)
    check_every_signal_is_carried(oStandard, list(dCarriers), sInterfaceFile, 'the interface file has no port or clock')


def can_share_signal(tFirst, tSecond):
    # Two clocks of one port, such as a write clock and a slower read clock, carry the same signal.
    if not tFirst[0].startswith('clock') or not tSecond[0].startswith('clock'):
        return False
    return tFirst[1] == tSecond[1]


def collect_device_pins(oInterface):
    # The device pin each signal crosses the board at: a port, or the port of a clock.
    lPins = []
    for oClock in oInterface.clocks:
        if oClock.if_signal is not None:
            lPins.append((f'clock {oClock.name}', oClock.if_signal, oClock.port))
    for oPort in oInterface.ports:
        if oPort.if_signal is not None:
            lPins.append((f'port {oPort.name}', oPort.if_signal, oPort.name))
    return lPins


def check_part_signals(oStandard, oInterface, oPartInterface):
    lSignals = []
    for oPin in collect_part_pins(oPartInterface):
        if oPin.if_signal is None:
            continue
        sDescription = f'pin {oPin.name} of part interface {oPartInterface.name}'
        check_signal_name(oStandard, oPin.if_signal, oInterface.part, sDescription)
        if oPin.if_signal in lSignals:
            raise_error(5, oInterface.part, f'{sDescription} gives if_signal {oPin.if_signal}, which another pin of the interface gives; a signal is carried by one pin')
        lSignals.append(oPin.if_signal)
    check_every_signal_is_carried(oStandard, lSignals, oInterface.part, f'part interface {oPartInterface.name} has no pin')


def check_trace_signals(oStandard, oInterface, oTraceList):
    lSignals = []
    for oTrace in oTraceList.traces:
        if oTrace.if_signal is None:
            continue
        check_signal_name(oStandard, oTrace.if_signal, oInterface.traces, f'trace {oTrace.name}')
        if oTrace.if_signal in lSignals:
            raise_error(5, oInterface.traces, f'trace {oTrace.name} gives if_signal {oTrace.if_signal}, which another trace gives; a signal is carried by one trace')
        lSignals.append(oTrace.if_signal)
    check_every_signal_is_carried(build_standard_without_source_clocks(oStandard), lSignals, oInterface.traces, 'the traces file has no trace')


def build_standard_without_source_clocks(oStandard):
    # A clock from a source reaches each end on a trace that names its pin, so no trace gives its signal.
    lSignals = []
    for oSignal in oStandard.signals:
        if not oSignal.is_from_source():
            lSignals.append(oSignal)
    return standards.Standard(oStandard.name, oStandard.roles, lSignals, oStandard.idle, oStandard.change_edge, oStandard.sample_edge)


def check_every_signal_is_carried(oStandard, lSignals, sFilename, sDescription):
    # A repeated signal is carried at least once, under any number.
    lNames = []
    for sSignal in lSignals:
        lNames.append(oStandard.get_signal(sSignal).name)
    for oSignal in oStandard.signals:
        if oSignal.optional:
            continue
        if oSignal.name not in lNames:
            raise_error(9, sFilename, f'{sDescription} with if_signal {oSignal.name}, a signal of {oStandard.name}')


def link_traces(sInterfaceFile, oInterface, oTraceList, oPartInterface):
    for oTrace in oTraceList.traces:
        if oTrace.if_signal is None:
            continue
        oTrace.device_pin = find_device_pin(oInterface, oTrace.if_signal)
        if oTrace.device_pin is None:
            raise_error(7, sInterfaceFile, f'has no port or clock with if_signal {oTrace.if_signal}, which trace {oTrace.name} carries')
        oTrace.part_pin = find_part_pin(oPartInterface, oTrace.if_signal)
        if oTrace.part_pin is None:
            raise_error(8, oInterface.part, f'part interface {oPartInterface.name} has no pin with if_signal {oTrace.if_signal}, which trace {oTrace.name} carries')


def collect_part_pins(oPartInterface):
    # The clock pins and the pins of the part interface, each with its name and signal.
    lPins = list(oPartInterface.clock_pins)
    lPins.extend(oPartInterface.pins.pins)
    return lPins


def find_part_pin(oPartInterface, sSignal):
    for oPin in collect_part_pins(oPartInterface):
        if oPin.if_signal == sSignal:
            return oPin.name
    return None


def find_device_pin(oInterface, sSignal):
    for sDescription, sPinSignal, sDevicePin in collect_device_pins(oInterface):
        if sPinSignal == sSignal:
            return sDevicePin
    return None


def check_directions(oStandard, sInterfaceFile, oInterface, oTraceList, oPartInterface):
    # Each signal goes from the role that drives it to the other.
    for oTrace in oTraceList.traces:
        if oTrace.if_signal is not None:
            check_trace_direction(oStandard, oInterface, oTrace)
    for oPort in oInterface.get_analyzed_ports():
        if oPort.if_signal is not None:
            check_port_direction(oStandard, sInterfaceFile, oInterface, oPort)
    for oPin in oPartInterface.pins.pins:
        if oPin.if_signal is not None:
            check_pin_direction(oStandard, oInterface, oPartInterface, oPin)


def device_drives(oStandard, oInterface, sSignal):
    return oStandard.get_signal(sSignal).driver == oInterface.if_role


def check_trace_direction(oStandard, oInterface, oTrace):
    sDriver = oStandard.get_signal(oTrace.if_signal).driver
    sStart = f'trace {oTrace.name} carries {oTrace.if_signal}, which the {sDriver} drives, and the device is the {oInterface.if_role}'
    if device_drives(oStandard, oInterface, oTrace.if_signal):
        if oTrace.device_to_part is None or oTrace.part_to_device is not None:
            raise_error(10, oInterface.traces, f'{sStart}, so the trace gives device_to_part and not part_to_device')
    elif oTrace.part_to_device is None or oTrace.device_to_part is not None:
        raise_error(10, oInterface.traces, f'{sStart}, so the trace gives part_to_device and not device_to_part')


def check_port_direction(oStandard, sInterfaceFile, oInterface, oPort):
    oSignal = oStandard.get_signal(oPort.if_signal)
    if oSignal.kind == standards.CLOCK:
        return
    sExpected = methodology.INPUT
    if device_drives(oStandard, oInterface, oPort.if_signal):
        sExpected = methodology.OUTPUT
    if oPort.data_direction != sExpected:
        raise_error(11, sInterfaceFile, f'port {oPort.name} carries {oPort.if_signal}, which the {oSignal.driver} drives, and the device is the {oInterface.if_role}, so the port is an {sExpected}; methodology {oPort.methodology} times an {oPort.data_direction}')


def check_pin_direction(oStandard, oInterface, oPartInterface, oPin):
    oSignal = oStandard.get_signal(oPin.if_signal)
    bPartDrives = oSignal.driver == oPartInterface.if_role
    if bPartDrives == part.is_input_pin(oPin):
        sExpected = 'an input'
        if bPartDrives:
            sExpected = 'an output'
        raise_error(11, oInterface.part, f'pin {oPin.name} of part interface {oPartInterface.name} carries {oPin.if_signal}, which the {oSignal.driver} drives, and the part is the {oPartInterface.if_role}, so the pin is {sExpected}; methodology {oPin.methodology} is not')


def check_edges(oStandard, sInterfaceFile, oInterface, oPartInterface):
    for oClock in oInterface.clocks:
        if oClock.if_signal is not None and oClock.idle is not None and oStandard.idle is not None and oClock.idle != oStandard.idle:
            raise_error(12, sInterfaceFile, f'clock {oClock.name} idles {oClock.idle}, but the clock of {oStandard.name} idles {oStandard.idle}')
    for oPort in oInterface.get_analyzed_ports():
        if oPort.if_signal is not None:
            check_port_edges(oStandard, sInterfaceFile, oInterface, oPort)
    for oPin in oPartInterface.pins.pins:
        if oPin.if_signal is not None:
            check_pin_edges(oStandard, oInterface, oPartInterface, oPin)


def check_port_edges(oStandard, sInterfaceFile, oInterface, oPort):
    # The edges of the clock that crosses the board: the part samples on the capture edges of a clock the device
    # forwards to capture with, and the data changes on the launch edges of a clock it is launched with.
    oClock = oInterface.get_clock_named(oPort.forwarded_clock.name)
    if oClock is None or oClock.if_signal is None:
        return
    if oPort.forwarded_clock_key == methodology.CAPTURE_CLOCK:
        lEdges = [find_capture_edge_type(oPort.forwarded_clock.setup_edge), find_capture_edge_type(oPort.forwarded_clock.hold_edge)]
        check_port_edge_types(oPort, lEdges, oStandard.sample_edge, 'samples', sInterfaceFile, oStandard)
    else:
        lEdges = [find_launch_edge_type(oPort.forwarded_clock.setup_edge), find_launch_edge_type(oPort.forwarded_clock.hold_edge)]
        check_port_edge_types(oPort, lEdges, oStandard.change_edge, 'changes', sInterfaceFile, oStandard)


def check_port_edge_types(oPort, lEdges, sExpected, sVerb, sFilename, oStandard):
    for sEdge in lEdges:
        if sEdge != sExpected:
            raise_error(12, sFilename, f'port {oPort.name} uses {sEdge.lower()} edges of {oPort.forwarded_clock.name}, but {oStandard.name} {sVerb} data on {sExpected.lower()} edges')


def find_capture_edge_type(iEdgeNumber):
    return find_edge_type(iEdgeNumber)


def find_launch_edge_type(iEdgeNumber):
    return find_edge_type(iEdgeNumber)


def find_edge_type(iEdgeNumber):
    # Each clock rises at edge 0.
    if iEdgeNumber % 2 == 0:
        return standards.RISING
    return standards.FALLING


def check_pin_edges(oStandard, oInterface, oPartInterface, oPin):
    sDescription = f'pin {oPin.name} of part interface {oPartInterface.name}'
    if part.is_input_pin(oPin) and oPin.capture_edge != oStandard.sample_edge:
        raise_error(12, oInterface.part, f'{sDescription} captures on the {oPin.capture_edge.lower()} edge, but {oStandard.name} samples data on the {oStandard.sample_edge.lower()} edge')
    if not part.is_input_pin(oPin) and oPin.launch_edge != oStandard.change_edge:
        raise_error(12, oInterface.part, f'{sDescription} launches on the {oPin.launch_edge.lower()} edge, but {oStandard.name} changes data on the {oStandard.change_edge.lower()} edge')


def join_names(lNames):
    if len(lNames) == 1:
        return lNames[0]
    return ', '.join(lNames[:-1]) + ' or ' + lNames[-1]
