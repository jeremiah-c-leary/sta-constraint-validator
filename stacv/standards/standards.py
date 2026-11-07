'''
The interface standards stacv knows: their roles, their signals, and the clock edges the signals change and are sampled on.

An interface file, and a part interface, can name the standard they follow with if_standard and their role in it with
if_role; each clock, port, part pin and trace then names the signal it carries with if_signal.  The signals link the
three files together, and let stacv check the interface against the standard.

A signal that can repeat, such as the chip select of a bus with several parts, is numbered with a dot: CS.1, CS.2.
'''

CONTROLLER = 'controller'
PERIPHERAL = 'peripheral'
RISING = 'Rising'
FALLING = 'Falling'
CLOCK = 'clock'
DATA = 'data'
SIGNAL_NUMBER_SEPARATOR = '.'


class Signal():
    '''
    A signal of a standard: whether it is a clock or data, the role that drives it, and whether it can repeat.
    '''

    def __init__(self, sName, sKind, sDriver, bRepeats):
        self.name = sName
        self.kind = sKind
        self.driver = sDriver
        self.repeats = bRepeats


class Standard():
    '''
    A standard with one clock: the level the clock idles at, and the edges data changes and is sampled on.
    '''

    def __init__(self, sName, lRoles, lSignals, sIdle, sChangeEdge, sSampleEdge):
        self.name = sName
        self.roles = lRoles
        self.signals = lSignals
        self.idle = sIdle
        self.change_edge = sChangeEdge
        self.sample_edge = sSampleEdge

    def get_signal(self, sSignal):
        # CS.2 is the signal CS.
        sName = sSignal.split(SIGNAL_NUMBER_SEPARATOR)[0]
        for oSignal in self.signals:
            if oSignal.name == sName:
                return oSignal
        return None

    def get_signal_names(self):
        lNames = []
        for oSignal in self.signals:
            lNames.append(oSignal.name)
        return lNames

    def get_other_role(self, sRole):
        for sOtherRole in self.roles:
            if sOtherRole != sRole:
                return sOtherRole
        return None


def build_spi_signals():
    # The signal names of the Open Source Hardware Association's 2020 resolution.
    lSignals = []
    lSignals.append(Signal('SCK', CLOCK, CONTROLLER, False))
    lSignals.append(Signal('COPI', DATA, CONTROLLER, False))
    lSignals.append(Signal('CIPO', DATA, PERIPHERAL, False))
    lSignals.append(Signal('CS', DATA, CONTROLLER, True))
    return lSignals


def build_spi_mode(iMode):
    # CPOL sets the level the clock idles at, so the first edge of a transfer, the leading edge, rises from low or falls
    # from high.  CPHA 0 samples on the leading edge and changes on the trailing edge; CPHA 1 the other way round.
    iClockPolarity = iMode // 2
    iClockPhase = iMode % 2
    sIdle = 'low'
    sLeadingEdge = RISING
    sTrailingEdge = FALLING
    if iClockPolarity == 1:
        sIdle = 'high'
        sLeadingEdge = FALLING
        sTrailingEdge = RISING
    if iClockPhase == 0:
        return Standard(f'SPI mode {iMode}', [CONTROLLER, PERIPHERAL], build_spi_signals(), sIdle, sTrailingEdge, sLeadingEdge)
    return Standard(f'SPI mode {iMode}', [CONTROLLER, PERIPHERAL], build_spi_signals(), sIdle, sLeadingEdge, sTrailingEdge)


def build_standards():
    dStandards = {}
    for iMode in range(4):
        oStandard = build_spi_mode(iMode)
        dStandards[oStandard.name] = oStandard
    return dStandards


STANDARDS = build_standards()


def get_standard(sName):
    return STANDARDS.get(sName)


def get_standard_names():
    return list(STANDARDS)
