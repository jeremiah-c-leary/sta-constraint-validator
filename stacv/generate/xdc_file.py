'''
Writes the Vivado timing constraints file of an interface, with the context a reader needs.
'''

from stacv import version
from stacv.generate import xdc
from stacv.generate import xdc_section
from stacv.inputs import port_profile
from stacv.interface import port
from stacv.output import md5sum_table
from stacv.output import number_format
from stacv.output import text_table
from stacv.rules import edge_times
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
    lCommands = xdc.generate_port_constraints(oPortProfile)
    lContent = ['#']
    lContent.extend(comment_lines(edges.draw_edge_diagram(oPort)))
    lContent.append('#')
    lContent.extend(build_requirement_lines(oPort))
    lContent.append('#')
    lContent.append('#' + '-' * 78)
    for sCommand in lCommands:
        lContent.extend(build_command_block([], sCommand))
    return lContent


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
