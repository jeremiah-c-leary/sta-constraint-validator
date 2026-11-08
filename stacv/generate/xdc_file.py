'''
Writes the Vivado timing constraints file of an interface, with the context a reader needs.
'''

from stacv import version
from stacv.generate import xdc
from stacv.generate import xdc_section
from stacv.inputs import port_profile
from stacv.interface import port
from stacv.methodology import methodology
from stacv.methodology import methodology_factory
from stacv.output import md5sum_table
from stacv.output import number_format
from stacv.output import text_table
from stacv.part import part
from stacv.rules import edge_times
from stacv.rules import input_delays
from stacv.rules import output_delays
from stacv.rules import path_lookups
from stacv.rules import port_delays
from stacv.rules import requirements
from stacv.spi import spi_config
from stacv.visualize import block_diagram
from stacv.visualize import edge_window
from stacv.visualize import edges

BANNER = '#' * 79
FALLING_EDGE_OPTIONS = '-clock_fall -add_delay'
TABLE_COLUMN_GAP = 2


def generate_file(sInterfaceFile, oInterface, oTraceList, oPart):
    lSections = build_sections(sInterfaceFile, oInterface, oTraceList, oPart)
    lLines = []
    lLines.extend(build_header(oInterface))
    lLines.extend(build_table_of_contents(lSections))
    for oSection in lSections:
        lLines.extend(build_section_lines(oSection))
    return remove_trailing_separators(lLines)


def build_sections(sInterfaceFile, oInterface, oTraceList, oPart):
    lSections = []
    lSections.append(xdc_section.Section('1', 'References', build_references(sInterfaceFile, oInterface, oPart)))
    lSections.append(xdc_section.Section('2', 'Block Diagram', build_block_diagram(oInterface, oTraceList, oPart)))
    lSections.append(xdc_section.Section('3', 'Inputs', None))
    lSections.append(xdc_section.Section('3.1', 'Trace Delays', build_trace_delays(oInterface, oTraceList)))
    lSections.append(xdc_section.Section('3.2', 'Part Timing', build_part_timing(oInterface, oTraceList, oPart)))
    lSections.append(xdc_section.Section('4', 'Clocks', None))
    lSections.extend(build_generated_clock_sections(oInterface))
    lSections.append(xdc_section.Section('5', 'Ports', None))
    lSections.extend(build_port_sections(oInterface, oTraceList, oPart))
    return lSections


def build_references(sInterfaceFile, oInterface, oPart):
    lFiles = [sInterfaceFile, oInterface.part, oInterface.traces]
    lLines = ['#']
    lLines.extend(comment_lines(md5sum_table.build_md5sum_table(lFiles)))
    lLines.append('#')
    lLines.append(f'# Part:       {oPart.manufacturer} {oPart.part_number}')
    lLines.append(f'# Datasheet:  {oPart.datasheet.name}')
    lLines.append(f'# Revision:   {oPart.datasheet.version}')
    lLines.append(f'# URL:        {oPart.datasheet.url}')
    lLines.extend(build_edge_lines(oInterface))
    lLines.append('#')
    return lLines


def build_edge_lines(oInterface):
    # An interface configuration file gives each edge with where in the design it comes from.
    if len(oInterface.edge_lines) == 0:
        return []
    lLines = [f'# Edges:      {spi_config.EDGES_HEADING}']
    for sLine in oInterface.edge_lines:
        lLines.append(f'#             {sLine}')
    return lLines


def build_block_diagram(oInterface, oTraceList, oPart):
    lLines = ['#']
    lLines.extend(comment_lines(block_diagram.draw_block_diagram(oInterface, oTraceList, oPart)))
    lLines.append('#')
    return lLines


def build_trace_delays(oInterface, oTraceList):
    lRows = [['Trace', 'From', 'To', 'Maximum (ns)', 'Minimum (ns)', 'Default']]
    for oTrace in block_diagram.select_traces(oInterface, oTraceList):
        if oTrace.device_to_part is not None:
            lRows.append(build_trace_delay_row(oTrace.name, oTrace.device_pin, oTrace.part_pin, oTrace.device_to_part))
        if oTrace.part_to_device is not None:
            lRows.append(build_trace_delay_row(oTrace.name, oTrace.part_pin, oTrace.device_pin, oTrace.part_to_device))
        if oTrace.source_to_device is not None:
            lRows.append(build_trace_delay_row(oTrace.name, oTrace.source, oTrace.device_pin, oTrace.source_to_device))
        if oTrace.source_to_part is not None:
            lRows.append(build_trace_delay_row(oTrace.name, oTrace.source, oTrace.part_pin, oTrace.source_to_part))
    lLines = ['#']
    lLines.extend(comment_lines(text_table.format_table(lRows, TABLE_COLUMN_GAP)))
    lLines.append('#')
    return lLines


def build_trace_delay_row(sName, sFrom, sTo, oTraceDelay):
    lRow = [sName, sFrom, sTo]
    lRow.append(number_format.format_number(oTraceDelay.max_delay))
    lRow.append(number_format.format_number(oTraceDelay.min_delay))
    lRow.append(format_yes_or_no(oTraceDelay.is_default))
    return lRow


def build_part_timing(oInterface, oTraceList, oPart):
    lRows = [['Pin', 'Timing', 'Value (ns)', 'Symbol', 'Source']]
    for oPin in find_part_pins(oInterface, oTraceList, oPart):
        if len(lRows) > 1:
            lRows.append(['', '', '', '', ''])
        lRows.extend(build_part_timing_rows(oPin))
    lLines = ['#']
    lLines.extend(comment_lines(text_table.format_table(lRows, TABLE_COLUMN_GAP)))
    lLines.append('#')
    return lLines


def find_part_pins(oInterface, oTraceList, oPart):
    # The part pins the traces reach, once each, in the order of the traces.
    # A port picks the pin of its methodology, so a bidirectional pin is listed for each direction.
    lPins = []
    for oTrace in block_diagram.select_traces(oInterface, oTraceList):
        for oPin in find_trace_pins(oInterface, oTrace, oPart):
            if oPin not in lPins:
                lPins.append(oPin)
    return lPins


def find_trace_pins(oInterface, oTrace, oPart):
    lPins = []
    for oPort in oInterface.get_analyzed_ports():
        if oPort.name == oTrace.device_pin:
            add_pin(lPins, oPart.get_pin_named(oTrace.part_pin, oPort.part_pin_methodology))
    if len(lPins) == 0:
        add_pin(lPins, oPart.get_pin_named(oTrace.part_pin))
    return lPins


def add_pin(lPins, oPin):
    if oPin is not None:
        lPins.append(oPin)


def build_part_timing_rows(oPin):
    # Each pin is listed in the form the part file gives it.
    lRows = []
    for sTiming in ['setup', 'hold', 'cko_max', 'cko_min', 'valid_before', 'valid_after']:
        oConstraint = getattr(oPin, sTiming)
        if oConstraint is not None:
            lRows.append(build_part_timing_row(oPin, sTiming, oConstraint))
    return lRows


def build_part_timing_row(oPin, sTiming, oConstraint):
    return [oPin.name, sTiming, number_format.format_number(oConstraint.value), oConstraint.symbol, oConstraint.source]


def format_yes_or_no(bValue):
    if bValue:
        return 'Yes'
    return 'No'


def comment_lines(lLines):
    lComments = []
    for sLine in lLines:
        lComments.append(('# ' + sLine).rstrip())
    return lComments


def build_generated_clock_sections(oInterface):
    # Each clock that crosses the board is defined once, in the order the ports first use it:
    # generated where the device generates it, or created on the port it enters the device on.
    lSections = []
    lClocks = []
    lGeneratedClocks = []
    for oPort in oInterface.get_analyzed_ports():
        if not is_generated(lClocks, oPort.forwarded_clock):
            lClocks.append(oPort.forwarded_clock)
            sNumber = f'4.{len(lClocks)}'
            if xdc.is_generated(oPort):
                lSections.append(build_generated_clock_section(sNumber, oPort, oInterface, lGeneratedClocks))
            else:
                lSections.append(build_created_clock_section(sNumber, oPort))
    return lSections


def build_generated_clock_section(sNumber, oPort, oInterface, lGeneratedClocks):
    bAdd = has_clock_generated_at_the_same_pin(lGeneratedClocks, oPort)
    lGeneratedClocks.append(oPort.forwarded_clock)
    sCommand = xdc.create_generated_clock(oPort, oInterface, bAdd)
    lComments = build_argument_comments(build_generated_clock_arguments(oPort, oInterface, bAdd))
    lContent = build_command_block(lComments, sCommand)
    return xdc_section.Section(sNumber, f'{oPort.forwarded_clock.name} Generated Clock', lContent)


def build_created_clock_section(sNumber, oPort):
    oClock = oPort.forwarded_clock
    lArguments = []
    lArguments.append(('-name', ['the name of the clock']))
    lArguments.append(('-period', [f'{oClock.name} period, {format_nanoseconds(oClock.period)}']))
    lArguments.append(('objects', [f'the port the clock enters the device on, {describe_clock_origin(oPort)}']))
    lContent = build_command_block(build_argument_comments(lArguments), xdc.create_clock(oClock))
    return xdc_section.Section(sNumber, f'{oClock.name} Clock', lContent)


def describe_clock_origin(oPort):
    if oPort.clock_origin == methodology.PART_CLOCK:
        return 'from the part'
    return 'from a clock source that also drives the part'


def is_generated(lGeneratedClocks, oClock):
    for oGeneratedClock in lGeneratedClocks:
        if oGeneratedClock.name == oClock.name:
            return True
    return False


def has_clock_generated_at_the_same_pin(lGeneratedClocks, oPort):
    xdc.check_generator_exists(oPort)
    for oGeneratedClock in lGeneratedClocks:
        if xdc.is_generated_at_the_same_pin(oGeneratedClock.generator, oPort.forwarded_clock.generator):
            return True
    return False


def build_generated_clock_arguments(oPort, oInterface, bAdd):
    oForwardedClock = oPort.forwarded_clock
    oGenerator = oForwardedClock.generator
    lArguments = []
    if bAdd:
        lArguments.append(('-add', ['allows for more than one clock to be generated from the same target']))
        lArguments.append(('-master_clock', ['the name of the source clock']))
    lArguments.append(('-name', ['the name of the generated clock']))
    lArguments.append(('-source', [f'{oForwardedClock.name} is generated by {oGenerator.source}, from {oGenerator.master_clock} at pin {oGenerator.master_pin} to pin {oGenerator.target_pin}']))
    lArguments.append(build_ratio_argument(oForwardedClock, oInterface.get_clock_named(oGenerator.master_clock)))
    lArguments.append(('objects', ['where the generated clock starts']))
    return lArguments


def build_ratio_argument(oForwardedClock, oMasterClock):
    if oForwardedClock.period < oMasterClock.period:
        return ('-multiply_by', build_period_ratio(oMasterClock, oForwardedClock))
    return ('-divide_by', build_period_ratio(oForwardedClock, oMasterClock))


def build_period_ratio(oLongerClock, oShorterClock):
    lLines = []
    lLines.append(f'{oLongerClock.name} period / {oShorterClock.name} period')
    lLines.append(f'{format_nanoseconds(oLongerClock.period)} / {format_nanoseconds(oShorterClock.period)}')
    lLines.append(str(xdc.calculate_ratio(oLongerClock.period, oShorterClock.period)))
    return lLines


def format_nanoseconds(fTime):
    return f'{number_format.format_number(fTime)} ns'


def build_argument_comments(lArguments):
    # Each argument is explained once, with its text aligned after the longest label.
    iWidth = find_longest_label(lArguments) + len(':') + 2
    lLines = []
    for sLabel, lText in lArguments:
        lLines.append(f'# {(sLabel + ":").ljust(iWidth)}{lText[0]}')
        for sText in lText[1:]:
            lLines.append(f'# {" " * iWidth}{sText}')
    return lLines


def find_longest_label(lArguments):
    iLongest = 0
    for sLabel, lText in lArguments:
        iLongest = max(iLongest, len(sLabel))
    return iLongest


def build_port_sections(oInterface, oTraceList, oPart):
    lSections = []
    for iPort, oPort in enumerate(oInterface.ports, start=1):
        lContent = build_port_content(oPort, oTraceList, oPart)
        if is_last_direction_of_bidirectional_port(oInterface, oPort):
            lContent.extend(build_bidirectional_false_path_block(oPort))
        lSections.append(xdc_section.Section(f'5.{iPort}', oPort.name, lContent))
    return lSections


def is_last_direction_of_bidirectional_port(oInterface, oPort):
    # A port timed both ways has an input delay and an output delay, which Vivado joins into a path through the pad.
    # The false path follows the last of the port's sections, once both directions are constrained.
    if oPort.status != port.ANALYZE:
        return False
    lDirections = []
    oLastPort = None
    for oOtherPort in oInterface.get_analyzed_ports():
        if oOtherPort.name == oPort.name:
            lDirections.append(oOtherPort.data_direction)
            oLastPort = oOtherPort
    if oLastPort is not oPort:
        return False
    return methodology.INPUT in lDirections and methodology.OUTPUT in lDirections


def build_bidirectional_false_path_block(oPort):
    sPort = xdc.format_port(oPort.name)
    lArguments = []
    lArguments.append(('-from', [f"{oPort.name} as an input, where the part's data arrives"]))
    lArguments.append(('-to', [f"{oPort.name} as an output, where the device's data leaves"]))
    lArguments.append(('reason', ['the input and output delays make the timing tool time a path from the port to itself', 'through the pad, which does not exist in the design.  Without the false path it is the', "worst hold path in the design, failing by the pad's input and output delays."]))
    return build_command_block(build_argument_comments(lArguments), f'set_false_path -from [get_ports {sPort}] -to [get_ports {sPort}]')



def build_port_content(oPort, oTraceList, oPart):
    if oPort.status == port.DEFER:
        return ['#', '# Deferred', '#']
    oPortProfile = port_profile.PortProfile(oPort, oTraceList, oPart, None)
    xdc.check_traces_exist(oPortProfile)
    if oPort.methodology in ['SDR-SS-O', 'SDR-SS-O-FLC', 'SDR-SS-RT-DI']:
        lDelayBlocks = build_delay_blocks(oPortProfile)
    else:
        lDelayBlocks = build_clock_crossing_delay_blocks(oPortProfile)
    lMulticycleBlocks = build_multicycle_blocks(oPort)
    lContent = ['#']
    lContent.extend(build_edge_windows(oPort))
    lContent.append('#')
    lContent.append('#' + '-' * 78)
    lContent.extend(lDelayBlocks)
    lContent.extend(lMulticycleBlocks)
    return lContent


def build_delay_blocks(oPortProfile):
    # Data the device sends gets output delays, and data it receives gets input delays.
    if xdc.is_input(oPortProfile.port):
        return build_input_delay_blocks(oPortProfile)
    return build_output_delay_blocks(oPortProfile)


def build_clock_crossing_delay_blocks(oPortProfile):
    # The methodologies whose clock comes from the part or a clock source, and double data rate.
    oPort = oPortProfile.port
    oMax, oMin = port_delays.calculate_delays(oPortProfile)
    sDelay = describe_delay(oPort)
    if xdc.is_input(oPort):
        fCreate = xdc.create_input_delay
    else:
        fCreate = xdc.create_output_delay
    lLines = []
    lMaxArguments = build_delay_clock_arguments(oPort)
    lMaxArguments.append(('-max', ['this is the setup check']))
    lMaxArguments.append((f'maximum {sDelay}', oMax.lines))
    lMaxArguments.append(('objects', [f'which data port the {sDelay} applies to']))
    lLines.extend(build_command_block(build_argument_comments(lMaxArguments), fCreate(oPort, '-max', oMax.value)))
    if oPort.double_data_rate:
        lLines.extend(build_falling_edge_max_delay_block(oPort, fCreate, oMax))
    lMinArguments = []
    lMinArguments.append(('-min', ['this is a hold check']))
    lMinArguments.append((f'minimum {sDelay}', oMin.lines))
    lLines.extend(build_command_block(build_argument_comments(lMinArguments), fCreate(oPort, '-min', oMin.value)))
    if oPort.double_data_rate:
        lLines.append(fCreate(oPort, '-min', oMin.value, FALLING_EDGE_OPTIONS))
        lLines.append('')
    return lLines


def build_falling_edge_max_delay_block(oPort, fCreate, oMax):
    # Double data rate data changes on both edges, so each delay is followed by the same delay for the falling edges.
    lArguments = []
    lArguments.append(('-clock_fall', [f'the same delays for the falling edges of {oPort.forwarded_clock.name}']))
    lArguments.append(('-add_delay', ['keeps the delays of the rising edges']))
    return build_command_block(build_argument_comments(lArguments), fCreate(oPort, '-max', oMax.value, FALLING_EDGE_OPTIONS))


def describe_delay(oPort):
    if xdc.is_input(oPort):
        return 'input delay'
    return 'output delay'


def build_delay_clock_arguments(oPort):
    lArguments = []
    if xdc.is_input(oPort):
        lArguments.append(('-clock', ['the launch clock']))
    else:
        lArguments.append(('-clock', ['the capture clock']))
    if not oPort.double_data_rate and xdc.forwarded_clock_setup_edge_is_falling(oPort):
        lArguments.append(('-clock_fall', [describe_falling_edges(oPort)]))
    if xdc.is_generated(oPort):
        lArguments.extend(build_reference_pin_argument(oPort))
    return lArguments


def build_output_delay_blocks(oPortProfile):
    sMaxOutputDelay = xdc.create_max_output_delay(oPortProfile)
    sMinOutputDelay = xdc.create_min_output_delay(oPortProfile)
    lLines = []
    lLines.extend(build_command_block(build_argument_comments(build_max_output_delay_arguments(oPortProfile)), sMaxOutputDelay))
    lLines.extend(build_command_block(build_argument_comments(build_min_output_delay_arguments(oPortProfile)), sMinOutputDelay))
    return lLines


def build_input_delay_blocks(oPortProfile):
    sMaxInputDelay = xdc.create_max_input_delay(oPortProfile)
    sMinInputDelay = xdc.create_min_input_delay(oPortProfile)
    lLines = []
    lLines.extend(build_command_block(build_argument_comments(build_max_input_delay_arguments(oPortProfile)), sMaxInputDelay))
    lLines.extend(build_command_block(build_argument_comments(build_min_input_delay_arguments(oPortProfile)), sMinInputDelay))
    return lLines


def build_edge_windows(oPort):
    # Each window of the edge diagram is followed by the requirements it shows.
    oMethodology = methodology_factory.create_methodology(oPort.methodology)
    lSetupLine, lHoldLine = build_requirement_lines(oPort)
    dRequirements = {edge_window.SETUP: lSetupLine, edge_window.HOLD: lHoldLine}
    lWindows = comment_windows(edges.draw_edge_diagram(oPort, oMethodology.edge_diagram_type))
    return edge_window.join_windows(lWindows, dRequirements, '#')


def comment_windows(lWindows):
    lCommentedWindows = []
    for oWindow in lWindows:
        lCommentedWindows.append(edge_window.EdgeWindow(comment_lines(oWindow.lines), oWindow.requirements))
    return lCommentedWindows


def build_multicycle_blocks(oPort):
    iSetupMulticycle = xdc.calculate_setup_multicycle(oPort)
    xdc.check_setup_multicycle(oPort, iSetupMulticycle)
    iHoldMulticycle = xdc.calculate_hold_multicycle(oPort)
    xdc.check_hold_multicycle(oPort, iHoldMulticycle)
    lLines = []
    if oPort.double_data_rate and iSetupMulticycle == 0:
        return build_same_edge_double_data_rate_blocks(oPort)
    if is_double_data_rate_input(oPort):
        lLines.extend(build_next_edge_double_data_rate_blocks(oPort))
    bSetupMulticycleWritten = iSetupMulticycle != 1
    if bSetupMulticycleWritten:
        lArguments = build_setup_multicycle_arguments(oPort, iSetupMulticycle)
        lLines.extend(build_command_block(build_argument_comments(lArguments), xdc.create_multicycle_path(oPort, iSetupMulticycle, '-setup')))
    if iHoldMulticycle != 0:
        lArguments = build_hold_multicycle_arguments(oPort, iHoldMulticycle)
        # The arguments both multicycles share are explained once, with the first one written.
        if not bSetupMulticycleWritten:
            lArguments.extend(build_shared_multicycle_arguments(oPort))
        lLines.extend(build_command_block(build_argument_comments(lArguments), xdc.create_multicycle_path(oPort, iHoldMulticycle, '-hold')))
    return lLines


def build_same_edge_double_data_rate_blocks(oPort):
    # Each edge captures the data it launches, after the clock's delay to the register:
    # the rising edge captures what the rising edge launched, and the falling edge what the falling edge launched.
    # The setup checks move back to that same edge; the hold checks are against the data the other edge launches next.
    lArguments = []
    lArguments.append(('multiplier', ['0: the data is captured on the edge that launches it', 'setup requirement 0 ns']))
    lArguments.append(('-setup', ['this is the setup multicycle, for the rising and the falling edges']))
    lArguments.append(('-end', ['multiplier is relative to the capturing clock']))
    lArguments.append(('-through', [f'the data port, so only its paths move']))
    lLines = []
    lCommands = []
    lCommands.append(xdc.create_edge_multicycle_path(oPort, 0, '-setup', 'rise', 'rise'))
    lCommands.append(xdc.create_edge_multicycle_path(oPort, 0, '-setup', 'fall', 'fall'))
    lLines.extend(build_command_block(build_argument_comments(lArguments), lCommands[0]))
    lLines.append(lCommands[1])
    lLines.append('')
    lFalseArguments = []
    lFalseArguments.append(('-setup', ['an edge does not capture the data the other edge launches']))
    lFalseArguments.append(('-hold', ['the hold check of an edge is against the data the other edge launches next,', 'so its own next data is not a hold check']))
    lCommands = []
    lCommands.append(xdc.create_edge_false_path(oPort, '-setup', 'rise', 'fall'))
    lCommands.append(xdc.create_edge_false_path(oPort, '-setup', 'fall', 'rise'))
    lCommands.append(xdc.create_edge_false_path(oPort, '-hold', 'rise', 'rise'))
    lCommands.append(xdc.create_edge_false_path(oPort, '-hold', 'fall', 'fall'))
    lLines.extend(build_command_block(build_argument_comments(lFalseArguments), lCommands[0]))
    for sCommand in lCommands[1:]:
        lLines.append(sCommand)
        lLines.append('')
    return lLines


def is_double_data_rate_input(oPort):
    # The data is launched on both edges of the part's clock, so the timing tool pairs each launch edge with each capture edge.
    return oPort.double_data_rate and xdc.is_input(oPort)


def build_next_edge_double_data_rate_blocks(oPort):
    # Each edge's data is captured on the next edge, of the other type: data launched on a rising edge is captured on a falling edge.
    # The setup checks are between edges of different types; the hold checks are against the data the same type of edge launches next.
    lArguments = []
    lArguments.append(('-setup', ['an edge does not capture the data the same type of edge launches']))
    lArguments.append(('-hold', ['the hold check of an edge is against the data the same type of edge launches next,', 'so the data the other type of edge launches is not a hold check']))
    lArguments.append(('-through', ['the data port, so only its paths are false']))
    lCommands = []
    lCommands.append(xdc.create_edge_false_path(oPort, '-setup', 'rise', 'rise'))
    lCommands.append(xdc.create_edge_false_path(oPort, '-setup', 'fall', 'fall'))
    lCommands.append(xdc.create_edge_false_path(oPort, '-hold', 'rise', 'fall'))
    lCommands.append(xdc.create_edge_false_path(oPort, '-hold', 'fall', 'rise'))
    lLines = []
    lLines.extend(build_command_block(build_argument_comments(lArguments), lCommands[0]))
    for sCommand in lCommands[1:]:
        lLines.append(sCommand)
        lLines.append('')
    return lLines


def build_setup_multicycle_arguments(oPort, iSetupMulticycle):
    sStep = describe_step_clock(oPort)
    fSetupRequirement = requirements.calculate_configuration_setup_requirement(oPort)
    lMultiplier = []
    lMultiplier.append(f'setup requirement / {sStep} period')
    lMultiplier.append(f'{format_nanoseconds(fSetupRequirement)} / {format_nanoseconds(xdc.find_step_period(oPort))}')
    lMultiplier.append(str(iSetupMulticycle))
    lArguments = []
    lArguments.append(('multiplier', lMultiplier))
    lArguments.append(('-setup', ['this is the setup multicycle']))
    lArguments.extend(build_shared_multicycle_arguments(oPort))
    return lArguments


def build_hold_multicycle_arguments(oPort, iHoldMulticycle):
    sStep = describe_step_clock(oPort)
    fSetupRequirement = requirements.calculate_configuration_setup_requirement(oPort)
    fHoldRequirement = requirements.calculate_configuration_hold_requirement(oPort)
    lMultiplier = []
    lMultiplier.append(f'(setup requirement - hold requirement) / {sStep} period - 1')
    lMultiplier.append(f'({format_nanoseconds(fSetupRequirement)} - {format_nanoseconds(fHoldRequirement)}) / {format_nanoseconds(xdc.find_step_period(oPort))} - 1')
    lMultiplier.append(str(iHoldMulticycle))
    lArguments = []
    lArguments.append(('multiplier', lMultiplier))
    lArguments.append(('-hold', ['this is the hold multicycle']))
    return lArguments


def build_shared_multicycle_arguments(oPort):
    lArguments = []
    lArguments.append((xdc.select_moved_edge(oPort), [describe_moved_edge(oPort)]))
    if xdc.is_input(oPort):
        lArguments.append(('-from', ['the port on the device that receives data from the part']))
        lArguments.append(('-to', ['the clock in the device that captures data']))
    else:
        lArguments.append(('-from', ['paths in the design that drive the output port']))
        lArguments.append(('-to', ['the output data port']))
    return lArguments


def describe_moved_edge(oPort):
    if xdc.launch_clock_is_faster(oPort):
        return 'multiplier is relative to the launching clock'
    return 'multiplier is relative to the capturing clock'


def describe_step_clock(oPort):
    # The multicycles count cycles of the faster clock.
    if xdc.launch_clock_is_faster(oPort):
        return 'launch'
    return 'capture'


def build_max_output_delay_arguments(oPortProfile):
    lArguments = build_forwarded_clock_arguments(oPortProfile.port, 'the capture clock')
    lArguments.append(('-max', ['this is the setup check']))
    lArguments.append(('maximum output delay', build_max_output_delay_calculation(oPortProfile)))
    lArguments.append(('objects', ['which data port the output delay applies to']))
    return lArguments


def build_max_input_delay_arguments(oPortProfile):
    lArguments = build_forwarded_clock_arguments(oPortProfile.port, 'the launch clock')
    lArguments.append(('-max', ['this is the setup check']))
    lArguments.append(('maximum input delay', build_max_input_delay_calculation(oPortProfile)))
    lArguments.append(('objects', ['which data port the input delay applies to']))
    return lArguments


def build_forwarded_clock_arguments(oPort, sClockDescription):
    # The delays are measured from the forwarded clock where it leaves the device.
    lArguments = []
    lArguments.append(('-clock', [sClockDescription]))
    if xdc.forwarded_clock_setup_edge_is_falling(oPort):
        lArguments.append(('-clock_fall', [describe_falling_edges(oPort)]))
    lArguments.extend(build_reference_pin_argument(oPort))
    return lArguments


def build_reference_pin_argument(oPort):
    oForwardedClock = oPort.forwarded_clock
    oGenerator = oForwardedClock.generator
    lReferencePin = []
    lReferencePin.append(f'{oForwardedClock.name} is generated at {oGenerator.source}/{oGenerator.target_pin}.  Without the reference pin,')
    lReferencePin.append(f'the delay from {oGenerator.target_pin} to {oForwardedClock.port} is left out of the clock path and the timing')
    lReferencePin.append('report is wrong without any warning.')
    return [('-reference_pin', lReferencePin)]


def describe_falling_edges(oPort):
    oForwardedClock = oPort.forwarded_clock
    sRole = describe_edge_role(oPort)
    if oForwardedClock.setup_edge == oForwardedClock.hold_edge:
        return f'the {sRole} edge {oForwardedClock.setup_edge} is a falling edge of {oForwardedClock.name}'
    return f'the {sRole} edges {oForwardedClock.setup_edge} and {oForwardedClock.hold_edge} are falling edges of {oForwardedClock.name}'


def build_max_output_delay_calculation(oPortProfile):
    oDataTrace, oPartPin, oClockTrace = find_output_delay_inputs(oPortProfile)
    lLines = []
    lLines.append(f'{oDataTrace.name} maximum - {oClockTrace.name} minimum + {oPartPin.name} setup')
    lLines.append(f'{format_value(oDataTrace.device_to_part.max_delay)} - {format_value(oClockTrace.device_to_part.min_delay)} + {format_value(oPartPin.setup.value)}')
    lLines.append(format_nanoseconds(output_delays.calculate_expected_max_output_delay(oPortProfile)))
    return lLines


def build_min_output_delay_arguments(oPortProfile):
    lArguments = []
    lArguments.append(('-min', ['this is a hold check']))
    lArguments.append(('minimum output delay', build_min_output_delay_calculation(oPortProfile)))
    return lArguments


def build_min_output_delay_calculation(oPortProfile):
    oDataTrace, oPartPin, oClockTrace = find_output_delay_inputs(oPortProfile)
    lLines = []
    lLines.append(f'{oDataTrace.name} minimum - {oClockTrace.name} maximum - {oPartPin.name} hold')
    lLines.append(f'{format_value(oDataTrace.device_to_part.min_delay)} - {format_value(oClockTrace.device_to_part.max_delay)} - {format_value(oPartPin.hold.value)}')
    lLines.append(format_nanoseconds(output_delays.calculate_expected_min_output_delay(oPortProfile)))
    return lLines


def describe_edge_role(oPort):
    if oPort.forwarded_clock_key == methodology.LAUNCH_CLOCK:
        return 'launch'
    return 'capture'


def build_max_input_delay_calculation(oPortProfile):
    oDataTrace, oPartPin, oClockTrace = input_delays.find_input_delay_inputs(oPortProfile)
    lLines = []
    lLines.append(f'{oClockTrace.name} maximum + part clock to out maximum + {oDataTrace.name} maximum')
    lLines.append(f'{format_value(oClockTrace.device_to_part.max_delay)} + {format_value(oPartPin.cko_max.value)} + {format_value(oDataTrace.part_to_device.max_delay)}')
    lLines.append(format_nanoseconds(input_delays.calculate_expected_max_input_delay(oPortProfile)))
    return lLines


def build_min_input_delay_arguments(oPortProfile):
    lArguments = []
    lArguments.append(('-min', ['this is a hold check']))
    lArguments.append(('minimum input delay', build_min_input_delay_calculation(oPortProfile)))
    return lArguments


def build_min_input_delay_calculation(oPortProfile):
    oDataTrace, oPartPin, oClockTrace = input_delays.find_input_delay_inputs(oPortProfile)
    lLines = []
    lLines.append(f'{oClockTrace.name} minimum + part clock to out minimum + {oDataTrace.name} minimum')
    lLines.append(f'{format_value(oClockTrace.device_to_part.min_delay)} + {format_value(oPartPin.cko_min.value)} + {format_value(oDataTrace.part_to_device.min_delay)}')
    lLines.append(format_nanoseconds(input_delays.calculate_expected_min_input_delay(oPortProfile)))
    return lLines


def find_output_delay_inputs(oPortProfile):
    oDataTrace = path_lookups.get_data_trace(oPortProfile)
    oPartPin = path_lookups.get_part_pin_at_end_of_trace(oPortProfile, oDataTrace)
    oClockTrace = path_lookups.get_clock_trace(oPortProfile, oPartPin)
    return oDataTrace, oPartPin, oClockTrace


def format_value(fValue):
    return number_format.format_number(fValue)


def build_requirement_lines(oPort):
    lRequirements = []
    lRequirements.append(build_setup_requirement(oPort))
    lRequirements.append(build_hold_requirement(oPort))
    iValueEnd = find_requirement_value_end(lRequirements)
    lLines = []
    for sLabel, sValue, sEdges in lRequirements:
        lLines.append(f'# {sLabel}{sValue.rjust(iValueEnd - len(sLabel))} ns ({sEdges})')
    return lLines


def build_setup_requirement(oPort):
    sValue = number_format.format_number(requirements.calculate_configuration_setup_requirement(oPort))
    sEdges = describe_edges(oPort, oPort.launch_clock.setup_edge, oPort.capture_clock.setup_edge)
    return ('setup requirement:', sValue, sEdges)


def build_hold_requirement(oPort):
    sValue = number_format.format_number(requirements.calculate_configuration_hold_requirement(oPort))
    sEdges = describe_edges(oPort, oPort.launch_clock.hold_edge, oPort.capture_clock.hold_edge)
    return ('hold requirement:', sValue, sEdges)


def find_requirement_value_end(lRequirements):
    # The values are right aligned, at least two spaces after the longest label.
    iValueEnd = 0
    for sLabel, sValue, sEdges in lRequirements:
        iValueEnd = max(iValueEnd, len(sLabel) + 2 + len(sValue))
    return iValueEnd


def describe_edges(oPort, iLaunchEdge, iCaptureEdge):
    fLaunchTime = edge_times.calculate_edge_time(oPort.launch_clock.period, iLaunchEdge)
    fCaptureTime = edge_times.calculate_edge_time(oPort.capture_clock.period, iCaptureEdge)
    return f'launch edge {iLaunchEdge} at {format_nanoseconds(fLaunchTime)} -> capture edge {iCaptureEdge} at {format_nanoseconds(fCaptureTime)}'


def build_command_block(lComments, sCommand):
    lLines = ['#']
    lLines.extend(lComments)
    lLines.append('#')
    lLines.append('')
    lLines.append(sCommand)
    lLines.append('')
    return lLines


def build_header(oInterface):
    lLines = []
    lLines.append(BANNER)
    lLines.append(f'#  {oInterface.interface_name}')
    lLines.append(BANNER)
    lLines.append('#')
    lLines.append(f'# This file is a timing constraints file for the {oInterface.interface_name} interface.')
    lLines.append(f'# Generated by stacv version {version.VERSION}')
    lLines.append('#')
    return lLines


def build_table_of_contents(lSections):
    lLines = []
    lLines.append('#  Table of contents')
    lLines.append('#')
    for oSection in lSections:
        lLines.append(f'#    Section {oSection.number}:  {oSection.title}')
    lLines.append('#')
    return lLines


def build_section_lines(oSection):
    # A section with subsections is only listed in the table of contents.
    if oSection.has_subsections():
        return []
    lLines = []
    lLines.append(BANNER)
    lLines.append(f'#  Section {oSection.number}:  {oSection.title}')
    lLines.append(BANNER)
    lLines.extend(oSection.content)
    return lLines


def remove_trailing_separators(lLines):
    while lLines[-1] in ['#', '']:
        lLines.pop()
    return lLines
