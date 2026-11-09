'''
Expands an RMII configuration into an interface file: the reference clock, and a port for each signal, timed
system synchronously on the rising edge of REF_CLK at both ends.

Every command reads the interface built from these lines, and stacv generate interface writes them, so the file a
user takes over is the interface stacv used.
'''

import os
import tomllib

from stacv.rmii import rmii_config
from stacv.spi import spi_interface

DOCS_URL = 'https://github.com/jeremiah-c-leary/sta-constraint-validator/blob/main/docs/source'
# The MAC drives the TX signals and captures the RX signals, both on the rising edge of REF_CLK.
METHODOLOGIES = {'TXD': 'SDR-SYS-O', 'TX_EN': 'SDR-SYS-O', 'TX_ER': 'SDR-SYS-O', 'RXD': 'SDR-SYS-I', 'CRS_DV': 'SDR-SYS-I', 'RX_ER': 'SDR-SYS-I'}
DIRECTIONS = {'SDR-SYS-O': 'from the MAC to the PHY', 'SDR-SYS-I': 'from the PHY to the MAC'}
# Launched on one rising edge of REF_CLK and captured on the next; held until the capture of the bit before.
LAUNCH_EDGE = 0
SETUP_CAPTURE_EDGE = 2
HOLD_CAPTURE_EDGE = 0


def build_interface_dictionary(oConfig):
    return tomllib.loads('\n'.join(build_interface_lines(oConfig)))


def build_interface_lines(oConfig):
    lLines = []
    lLines.extend(build_header(oConfig))
    lLines.extend(build_top_level_keys(oConfig))
    lLines.append('')
    lLines.extend(build_ref_clk(oConfig))
    for oSignal in oConfig.signals:
        lLines.append('')
        lLines.extend(build_port(oConfig, oSignal))
    return lLines


def build_header(oConfig):
    sConfigFile = os.path.basename(oConfig.filename)
    lLines = []
    lLines.append('# stacv interface file for an RMII interface, with the device as the MAC.')
    lLines.append(f'# Generated from {sConfigFile} by:  stacv generate interface {sConfigFile}')
    lLines.append('#')
    lLines.append('# Keys are described in:')
    lLines.append(f'# {DOCS_URL}/interface.rst')
    lLines.append('#')
    lLines.append('# Every signal changes and is sampled on the rising edge of the 50 MHz REF_CLK.')
    lLines.append('#')
    lLines.append(f'# Paths are relative to the folder of {sConfigFile}.')
    lLines.append('#')
    lLines.append('# All periods are in nanoseconds.')
    lLines.append('')
    return lLines


def build_top_level_keys(oConfig):
    lLines = []
    lLines.append('description = "RMII interface, with the device as the MAC"')
    lLines.append(f'name = {spi_interface.quote(oConfig.name)}')
    lLines.append(f'part = {spi_interface.quote(oConfig.part_as_written)}')
    lLines.append(f'part_interface = {spi_interface.quote(rmii_config.find_part_interface(oConfig))}')
    lLines.append(f'traces = {spi_interface.quote(oConfig.traces_as_written)}')
    lLines.append(f'if_standard = "{rmii_config.STANDARD}"')
    lLines.append(f'if_role = "{oConfig.role}"')
    return lLines


def build_ref_clk(oConfig):
    lLines = []
    lLines.append('# REF_CLK, received by the MAC.')
    lLines.append('[[clock]]')
    lLines.append(f'name = {spi_interface.quote(oConfig.ref_clk.name)}')
    lLines.append(f'period = {rmii_config.REF_CLK_PERIOD:.3f}')
    lLines.append(f'port = {spi_interface.quote(oConfig.ref_clk.port)}')
    lLines.append('if_signal = "REF_CLK"')
    return lLines


def build_port(oConfig, oSignal):
    sMethodology = METHODOLOGIES[oSignal.signal]
    sClock = spi_interface.quote(oConfig.ref_clk.name)
    lLines = []
    lLines.append(f'# {oSignal.signal}: data {DIRECTIONS[sMethodology]}.')
    lLines.append('[[port]]')
    lLines.append(f'name = {spi_interface.quote(oSignal.port)}')
    lLines.append(f'methodology = "{sMethodology}"')
    lLines.append(f'if_signal = "{oSignal.signal}"')
    lLines.append(f'launch_clock = {{name = {sClock}, setup_edge = {LAUNCH_EDGE}, hold_edge = {LAUNCH_EDGE}}}')
    lLines.append(f'capture_clock = {{name = {sClock}, setup_edge = {SETUP_CAPTURE_EDGE}, hold_edge = {HOLD_CAPTURE_EDGE}}}')
    lLines.append(f'registers = [{spi_interface.quote(oSignal.register)}]')
    lLines.append('timing_reports = [')
    lLines.append(f'    {spi_interface.quote(build_timing_report_path(oConfig, oSignal.signal))},')
    lLines.append(']')
    return lLines


def build_timing_report_path(oConfig, sSignal):
    sDirectory = oConfig.timing_reports_dir.rstrip('/')
    return f'{sDirectory}/{oConfig.name}.{sSignal}_timing.rpt'
