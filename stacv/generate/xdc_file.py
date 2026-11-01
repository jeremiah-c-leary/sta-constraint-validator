'''
Writes the Vivado timing constraints file of an interface, with the context a reader needs.
'''

from stacv import version
from stacv.generate import xdc
from stacv.generate import xdc_section
from stacv.inputs import port_profile
from stacv.interface import port
from stacv.methodology import methodology_factory
from stacv.output import md5sum_table
from stacv.output import number_format
from stacv.output import text_table
from stacv.rules import edge_times
from stacv.rules import output_delays
from stacv.rules import path_lookups
from stacv.rules import requirements
from stacv.visualize import block_diagram
from stacv.visualize import edges

BANNER = '#' * 79
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
    lSections.append(xdc_section.Section('4', 'Generated Clocks', None))
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
    lLines.append('#')
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
    lPins = []
    for oTrace in block_diagram.select_traces(oInterface, oTraceList):
        oPin = oPart.get_pin_named(oTrace.part_pin)
        if oPin is not None and oPin not in lPins:
            lPins.append(oPin)
    return lPins


def build_part_timing_rows(oPin):
    if oPin.methodology == 'SDR-SS-I':
        return [build_part_timing_row(oPin, 'setup', oPin.setup), build_part_timing_row(oPin, 'hold', oPin.hold)]
    return [build_part_timing_row(oPin, 'cko_max', oPin.cko_max), build_part_timing_row(oPin, 'cko_min', oPin.cko_min)]


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
    lSections = []
    lClockNames = []
    for oPort in oInterface.get_analyzed_ports():
        sClockName = oPort.capture_clock.name
        if sClockName not in lClockNames:
            lClockNames.append(sClockName)
            sNumber = f'4.{len(lClockNames)}'
            sCommand = xdc.create_generated_clock(oPort, oInterface)
            lComments = build_argument_comments(build_generated_clock_arguments(oPort, oInterface))
            lContent = build_command_block(lComments, sCommand)
            lSections.append(xdc_section.Section(sNumber, f'{sClockName} Generated Clock', lContent))
    return lSections


def build_generated_clock_arguments(oPort, oInterface):
    oCaptureClock = oPort.capture_clock
    oGenerator = oCaptureClock.generator
    lArguments = []
    lArguments.append(('-name', ['the name of the generated clock']))
    lArguments.append(('-source', [f'{oCaptureClock.name} is generated by {oGenerator.source}, from {oGenerator.master_clock} at pin {oGenerator.master_pin} to pin {oGenerator.target_pin}']))
    lArguments.append(build_ratio_argument(oCaptureClock, oInterface.get_clock_named(oGenerator.master_clock)))
    lArguments.append(('objects', ['where the generated clock starts']))
    return lArguments


def build_ratio_argument(oCaptureClock, oMasterClock):
    if oCaptureClock.period < oMasterClock.period:
        return ('-multiply_by', build_period_ratio(oMasterClock, oCaptureClock))
    return ('-divide_by', build_period_ratio(oCaptureClock, oMasterClock))


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
        lSections.append(xdc_section.Section(f'5.{iPort}', oPort.name, build_port_content(oPort, oTraceList, oPart)))
    return lSections


def build_port_content(oPort, oTraceList, oPart):
    if oPort.status == port.DEFER:
        return ['#', '# Deferred', '#']
    oPortProfile = port_profile.PortProfile(oPort, oTraceList, oPart, None)
    xdc.check_traces_exist(oPortProfile)
    sMaxOutputDelay = xdc.create_max_output_delay(oPortProfile)
    sMinOutputDelay = xdc.create_min_output_delay(oPortProfile)
    lMulticycleBlocks = build_multicycle_blocks(oPort)
    lContent = ['#']
    lContent.extend(build_edge_windows(oPort))
    lContent.append('#')
    lContent.append('#' + '-' * 78)
    lContent.extend(build_command_block(build_argument_comments(build_max_output_delay_arguments(oPortProfile)), sMaxOutputDelay))
    lContent.extend(build_command_block(build_argument_comments(build_min_output_delay_arguments(oPortProfile)), sMinOutputDelay))
    lContent.extend(lMulticycleBlocks)
    return lContent


def build_edge_windows(oPort):
    # Each window of the edge diagram is followed by the requirements it shows.
    oMethodology = methodology_factory.create_methodology(oPort.methodology)
    lSetupLine, lHoldLine = build_requirement_lines(oPort)
    dRequirements = {edges.edge_window.SETUP: lSetupLine, edges.edge_window.HOLD: lHoldLine}
    lLines = []
    for iIndex, oWindow in enumerate(edges.draw_edge_diagram(oPort, oMethodology.edge_diagram_type)):
        if iIndex > 0:
            lLines.append('#')
        lLines.extend(comment_lines(oWindow.lines))
        lLines.append('#')
        for sRequirement in oWindow.requirements:
            lLines.append(dRequirements[sRequirement])
    return lLines


def build_multicycle_blocks(oPort):
    iSetupMulticycle = xdc.calculate_setup_multicycle(oPort)
    xdc.check_setup_multicycle(oPort, iSetupMulticycle)
    iHoldMulticycle = xdc.calculate_hold_multicycle(oPort)
    xdc.check_hold_multicycle(oPort, iHoldMulticycle)
    lLines = []
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
    oCaptureClock = oPortProfile.port.capture_clock
    oGenerator = oCaptureClock.generator
    lArguments = []
    lArguments.append(('-clock', ['the capture clock']))
    if xdc.is_falling_edge(oCaptureClock.setup_edge):
        lArguments.append(('-clock_fall', [describe_falling_capture_edges(oCaptureClock)]))
    lReferencePin = []
    lReferencePin.append(f'{oCaptureClock.name} is generated at {oGenerator.source}/{oGenerator.target_pin}.  Without the reference pin,')
    lReferencePin.append(f'the delay from {oGenerator.target_pin} to {oCaptureClock.port} is left out of the clock path and the timing')
    lReferencePin.append('report is wrong without any warning.')
    lArguments.append(('-reference_pin', lReferencePin))
    lArguments.append(('-max', ['this is the setup check']))
    lArguments.append(('maximum output delay', build_max_output_delay_calculation(oPortProfile)))
    lArguments.append(('objects', ['which data port the output delay applies to']))
    return lArguments


def describe_falling_capture_edges(oCaptureClock):
    if oCaptureClock.setup_edge == oCaptureClock.hold_edge:
        return f'the capture edge {oCaptureClock.setup_edge} is a falling edge of {oCaptureClock.name}'
    return f'the capture edges {oCaptureClock.setup_edge} and {oCaptureClock.hold_edge} are falling edges of {oCaptureClock.name}'


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


def describe_edges(oPort, iLaunchEdge, sCaptureEdge):
    fLaunchTime = edge_times.calculate_edge_time(oPort.launch_clock.period, iLaunchEdge)
    iCaptureEdge = edge_times.convert_edge_letter_to_number(sCaptureEdge)
    fCaptureTime = edge_times.calculate_edge_time(oPort.capture_clock.period, iCaptureEdge)
    return f'launch edge {iLaunchEdge} at {format_nanoseconds(fLaunchTime)} -> capture edge {sCaptureEdge} at {format_nanoseconds(fCaptureTime)}'


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
