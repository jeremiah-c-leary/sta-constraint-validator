'''
The launch and capture edges of each SPI signal: the edges the SPI mode defines, moved by the adjust keys.

SCK is divided from the device clock, so each edge of SCK is a whole number of device clock edges apart, and every
edge is numbered on the device clock, edge 0 at SCK's edge A.  The mode defines, with SCK's first sample edge after
edge A:

    COPI   launched on the change edge before the first sample edge, captured on the sample edges either side of it
    CS     set one SCK period before the first sample edge, cleared at the change edge after the last
    CIPO   launched by the part on SCK's change edge, captured by the device at the sample edges either side of it

An adjust moves a launch, or for CIPO the device's captures, by a number of device clock edges: +1 is one edge later,
+2 one device clock period.
'''

from stacv.rules import edge_times
from stacv.standards import standards


class SpiEdges():

    def __init__(self, oConfig, oStandard):
        iEdgesPerSckEdge = round(oConfig.sck.period / oConfig.device_clock.period)
        # SCK rises at its edge 0, A, and falls at its edge 1, B.  The first sample edge is the first of the sample
        # kind after edge 0, so there is a change edge before it to launch on.
        iFirstSample = 2
        if oStandard.sample_edge == standards.FALLING:
            iFirstSample = 3
        iChange = iFirstSample - 1
        # SCK's edges, numbered on the device clock.
        self.first_sample_edge = iFirstSample * iEdgesPerSckEdge
        self.previous_sample_edge = (iFirstSample - 2) * iEdgesPerSckEdge
        self.change_edge = iChange * iEdgesPerSckEdge
        # COPI and CS are captured on SCK, so their capture edges are SCK's letters.
        self.sck_setup_capture = edge_times.convert_edge_number_to_letter(iFirstSample)
        self.sck_hold_capture = edge_times.convert_edge_number_to_letter(iFirstSample - 2)
        self.copi_launch = self.change_edge + oConfig.copi.adjust
        self.cs_setup_launch = self.previous_sample_edge + oConfig.cs.setup_adjust
        self.cs_hold_launch = self.change_edge + oConfig.cs.hold_adjust
        # CIPO is launched on SCK, so its launch edge is SCK's number, and captured on the device clock.
        self.cipo_launch = iChange
        self.cipo_setup_capture = self.first_sample_edge + oConfig.cipo.adjust
        self.cipo_hold_capture = self.previous_sample_edge + oConfig.cipo.adjust
