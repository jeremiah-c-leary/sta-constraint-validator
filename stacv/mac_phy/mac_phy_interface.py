'''
Expands an RMII or MII configuration into an interface file: the clocks the MAC receives, and a port for each signal,
launched on a rising edge of its clock and captured on the next.

Every command reads the interface built from these lines, and stacv generate interface writes them, so the file a
user takes over is the interface stacv used.
'''

import os
import tomllib

from stacv.mac_phy import mac_phy_config
from stacv.spi import spi_interface

DOCS_URL = 'https://github.com/jeremiah-c-leary/sta-constraint-validator/blob/main/docs/source'
# Launched on one rising edge of the clock and captured on the next; held until the capture of the bit before.
LAUNCH_EDGE = 0
SETUP_CAPTURE_EDGE = 2
HOLD_CAPTURE_EDGE = 0


def build_interface_dictionary(oConfig):
    return tomllib.loads('\n'.join(build_interface_lines(oConfig)))


def build_interface_lines(oConfig):
    lLines = []
    lLines.extend(build_header(oConfig))
    lLines.extend(build_top_level_keys(oConfig))
    for oClock in oConfig.clocks.values():
        lLines.append('')
        lLines.extend(build_clock(oClock))
    for oSignal in oConfig.signals:
        lLines.append('')
        lLines.extend(build_port(oConfig, oSignal))
    return lLines


def build_header(oConfig):
    sConfigFile = os.path.basename(oConfig.filename)
    lLines = []
    lLines.append(f'# stacv interface file for an {oConfig.protocol.standard} interface, with the device as the MAC.')
    lLines.append(f'# Generated from {sConfigFile} by:  stacv generate interface {sConfigFile}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/interface.rst')
    lLines.append('#')
    for sLine in oConfig.protocol.timing:
        lLines.append(f'# {sLine}')
    lLines.append('#')
    lLines.append(f'# Paths are relative to the folder of {sConfigFile}.')
    lLines.append('#')
    lLines.append('# All periods are in nanoseconds.')
    lLines.append('')
    return lLines


def build_top_level_keys(oConfig):
    lLines = []
    lLines.append(f'description = "{oConfig.protocol.standard} interface, with the device as the MAC"')
    lLines.append(f'name = {spi_interface.quote(oConfig.name)}')
    lLines.append(f'part = {spi_interface.quote(oConfig.part_as_written)}')
    lLines.append(f'part_interface = {spi_interface.quote(mac_phy_config.find_part_interface(oConfig))}')
    lLines.append(f'traces = {spi_interface.quote(oConfig.traces_as_written)}')
    lLines.append(f'if_standard = "{oConfig.protocol.standard}"')
    lLines.append(f'if_role = "{oConfig.role}"')
    return lLines


def build_clock(oClock):
    lLines = []
    lLines.append(f'# {oClock.clock.signal}, {oClock.clock.origin}.')
    lLines.append('[[clock]]')
    lLines.append(f'name = {spi_interface.quote(oClock.name)}')
    lLines.append(f'period = {oClock.clock.period:.3f}')
    lLines.append(f'port = {spi_interface.quote(oClock.port)}')
    lLines.append(f'if_signal = "{oClock.clock.signal}"')
    return lLines


def build_port(oConfig, oSignal):
    oDescription = oSignal.signal
    sClock = spi_interface.quote(oConfig.clocks[oDescription.clock_table].name)
    lLines = []
    lLines.append(f'# {oDescription.signal}: data {oConfig.protocol.directions[oDescription.methodology]}.')
    lLines.append('[[port]]')
    lLines.append(f'name = {spi_interface.quote(oSignal.port)}')
    lLines.append(f'methodology = "{oDescription.methodology}"')
    lLines.append(f'if_signal = "{oDescription.signal}"')
    lLines.append(f'launch_clock = {{name = {sClock}, setup_edge = {LAUNCH_EDGE}, hold_edge = {LAUNCH_EDGE}}}')
    lLines.append(f'capture_clock = {{name = {sClock}, setup_edge = {SETUP_CAPTURE_EDGE}, hold_edge = {HOLD_CAPTURE_EDGE}}}')
    lLines.append(f'registers = [{spi_interface.quote(oSignal.register)}]')
    lLines.append('timing_reports = [')
    lLines.append(f'    {spi_interface.quote(build_timing_report_path(oConfig, oDescription.signal))},')
    lLines.append(']')
    return lLines


def build_timing_report_path(oConfig, sSignal):
    sDirectory = oConfig.timing_reports_dir.rstrip('/')
    return f'{sDirectory}/{oConfig.name}.{sSignal}_timing.rpt'
