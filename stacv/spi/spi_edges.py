'''
The launch and capture edges of each SPI signal, from the SCK edge and the device clocks the configuration gives.

SCK is divided from the device clock, so each edge of SCK is a whole number of device clock edges apart, and every
edge is numbered on the device clock, edge 0 at SCK's edge A.  The SPI mode sets which SCK edges are change and sample
edges; the first sample edge is the first after edge A, so there is a change edge before it to launch on:

    COPI launch    counted from the change edge before the sample edge that captures it
    CIPO capture   counted from the sample edge after the change edge the part launches it on
    CS assert      counted from the first sample edge
    CS deassert    counted from the last change edge, or the last sample edge

A device clock has two edges, so each clock counted is two edges, and half a clock is a falling edge.
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
        oChipSelectDeassert = oConfig.cs.edges['deassert']
        self.copi_launch = self.change_edge + oConfig.copi.edges['launch'].count_device_clock_edges()
        self.cs_setup_launch = self.first_sample_edge + oConfig.cs.edges['assert'].count_device_clock_edges()
        self.cs_hold_launch = find_last_sck_edge(self, oChipSelectDeassert) + oChipSelectDeassert.count_device_clock_edges()
        # CIPO is launched on SCK, or on the slower read SCK, so its launch edge is that clock's number, and captured
        # on the device clock.
        iReadEdgesPerSckEdge = round(oConfig.sck.find_read_period() / oConfig.device_clock.period)
        iCaptureEdges = oConfig.cipo.edges['capture'].count_device_clock_edges()
        self.cipo_launch = iChange
        self.cipo_change_edge = iChange * iReadEdgesPerSckEdge
        self.cipo_setup_capture = iFirstSample * iReadEdgesPerSckEdge + iCaptureEdges
        self.cipo_hold_capture = (iFirstSample - 2) * iReadEdgesPerSckEdge + iCaptureEdges


def find_last_sck_edge(oEdges, oChipSelectDeassert):
    # CS is timed to the last sample edge at edge A, so the last change edge is the one after it.
    if oChipSelectDeassert.sck_edge == 'last sample':
        return oEdges.previous_sample_edge
    return oEdges.change_edge
