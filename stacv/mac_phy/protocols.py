'''
The MAC to PHY interfaces stacv has a configuration for, with the device as the MAC: their clocks, their signals, and
how each signal is timed.

The standard fixes everything else, so a configuration gives only the names in the design.  Every signal is launched
on a rising edge of its clock and captured on the next, at both ends.
'''

from stacv.config import config_reader
from stacv.mac_phy import mac_phy_config_error


class Clock():
    '''
    A clock the MAC receives: its table in the configuration, its signal, its period in ns, where it comes from, and
    whether it comes from a source that drives both ends on traces of their own.
    '''

    def __init__(self, sTable, sSignal, fPeriod, sOrigin, bFromSource):
        self.table = sTable
        self.signal = sSignal
        self.period = fPeriod
        self.origin = sOrigin
        self.from_source = bFromSource


class Signal():
    '''
    A data signal: its table in the configuration, its signal, whether an interface may leave it out, the table of the
    clock it is timed on, its methodology at the device, and its pin and methodology at the part.
    '''

    def __init__(self, sTable, sSignal, bOptional, sClockTable, sMethodology, sPartPin, sPartMethodology):
        self.table = sTable
        self.signal = sSignal
        self.optional = bOptional
        self.clock_table = sClockTable
        self.methodology = sMethodology
        self.part_pin = sPartPin
        self.part_methodology = sPartMethodology

    def is_from_mac(self):
        return self.methodology.endswith('-O') or self.methodology.endswith('-DO')


class Protocol():

    def __init__(self, sConfiguration, sStandard, lClocks, lSignals, dDirections, lTiming):
        # The value of the configuration's interface key, and the interface standard it follows.
        self.configuration = sConfiguration
        self.standard = sStandard
        self.reader = config_reader.ConfigReader(f'{sConfiguration}_config', mac_phy_config_error.MacPhyConfigError)
        self.clocks = lClocks
        self.signals = lSignals
        # Each methodology's direction, and how the protocol is timed, for the comments of the interface it expands to.
        self.directions = dDirections
        self.timing = lTiming

    def get_top_level_keys(self):
        lKeys = ['interface', 'name', 'role', 'part', 'traces', 'timing_reports_dir']
        for oClock in self.clocks:
            lKeys.append(oClock.table)
        for oSignal in self.signals:
            lKeys.append(oSignal.table)
        return lKeys


def build_rmii():
    # REF_CLK may come from the PHY, the MAC or an oscillator; both ends launch and capture on it.
    lClocks = [Clock('ref_clk', 'REF_CLK', 20.0, 'received by the MAC', True)]
    lSignals = []
    lSignals.append(Signal('txd', 'TXD', False, 'ref_clk', 'SDR-SYS-O', 'TXD[1:0]', 'SDR-SYS-I'))
    lSignals.append(Signal('tx_en', 'TX_EN', False, 'ref_clk', 'SDR-SYS-O', 'TX_EN', 'SDR-SYS-I'))
    lSignals.append(Signal('tx_er', 'TX_ER', True, 'ref_clk', 'SDR-SYS-O', 'TX_ER', 'SDR-SYS-I'))
    lSignals.append(Signal('rxd', 'RXD', False, 'ref_clk', 'SDR-SYS-I', 'RXD[1:0]', 'SDR-SYS-O'))
    lSignals.append(Signal('crs_dv', 'CRS_DV', False, 'ref_clk', 'SDR-SYS-I', 'CRS_DV', 'SDR-SYS-O'))
    lSignals.append(Signal('rx_er', 'RX_ER', True, 'ref_clk', 'SDR-SYS-I', 'RX_ER', 'SDR-SYS-O'))
    dDirections = {'SDR-SYS-O': 'from the MAC to the PHY', 'SDR-SYS-I': 'from the PHY to the MAC'}
    lTiming = ['Every signal changes and is sampled on the rising edge of the 50 MHz REF_CLK.']
    return Protocol('rmii', 'RMII', lClocks, lSignals, dDirections, lTiming)


def build_mii():
    # The PHY sends both clocks.  The MAC launches TXD on the TX_CLK it receives, a round trip back to the PHY, and
    # captures RXD with the RX_CLK sent with it.  At 10 Mbit/s the clocks are 2.5 MHz, with the same timing at the
    # pins, so timing at 25 MHz covers both speeds.
    lClocks = []
    lClocks.append(Clock('tx_clk', 'TX_CLK', 40.0, 'sent by the PHY', False))
    lClocks.append(Clock('rx_clk', 'RX_CLK', 40.0, 'sent by the PHY', False))
    lSignals = []
    lSignals.append(Signal('txd', 'TXD', False, 'tx_clk', 'SDR-SS-RT-DO', 'TXD[3:0]', 'SDR-SS-RT-DI'))
    lSignals.append(Signal('tx_en', 'TX_EN', False, 'tx_clk', 'SDR-SS-RT-DO', 'TX_EN', 'SDR-SS-RT-DI'))
    lSignals.append(Signal('tx_er', 'TX_ER', True, 'tx_clk', 'SDR-SS-RT-DO', 'TX_ER', 'SDR-SS-RT-DI'))
    lSignals.append(Signal('rxd', 'RXD', False, 'rx_clk', 'SDR-SS-I', 'RXD[3:0]', 'SDR-SS-O'))
    lSignals.append(Signal('rx_dv', 'RX_DV', False, 'rx_clk', 'SDR-SS-I', 'RX_DV', 'SDR-SS-O'))
    lSignals.append(Signal('rx_er', 'RX_ER', True, 'rx_clk', 'SDR-SS-I', 'RX_ER', 'SDR-SS-O'))
    dDirections = {'SDR-SS-RT-DO': 'from the MAC to the PHY, launched on TX_CLK', 'SDR-SS-I': 'from the PHY to the MAC, sent with RX_CLK'}
    lTiming = []
    lTiming.append('The PHY sends TX_CLK and RX_CLK, 25 MHz at 100 Mbit/s.  Every signal changes and is')
    lTiming.append('sampled on the rising edge of its clock.')
    return Protocol('mii', 'MII', lClocks, lSignals, dDirections, lTiming)


RMII = build_rmii()
MII = build_mii()
PROTOCOLS = [RMII, MII]


def get_protocol(sConfiguration):
    for oProtocol in PROTOCOLS:
        if oProtocol.configuration == sConfiguration:
            return oProtocol
    return None
