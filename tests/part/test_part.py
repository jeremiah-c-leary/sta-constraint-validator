import os
import tempfile
import unittest
from types import SimpleNamespace

from stacv.part import part


def build_part_text(sOutputMethodology):
    lText = []
    lText.append('[properties]')
    lText.append('manufacturer = "Texas Instruments"')
    lText.append('part_number = "ADC128S102"')
    lText.append('')
    lText.append('[datasheet]')
    lText.append('name = "ADC128S102"')
    lText.append('url = "https://www.ti.com/lit/ds/symlink/adc128s102.pdf"')
    lText.append('version = "SNAS298G"')
    lText.append('')
    lText.append('[[interface]]')
    lText.append('name = "Serial Interface"')
    lText.append('')
    lText.append('[[interface.pin]]')
    lText.append('name = "DOUT"')
    lText.append(f'methodology = "{sOutputMethodology}"')
    lText.append('clock = {pin = "SCLK", max_frequency = 16}')
    lText.append('cko_max = {value = 27, symbol = "tDACC", source = "6.6 Timing Specifications"}')
    lText.append('cko_min = {value = 0, symbol = "tDHLD", source = "6.6 Timing Specifications"}')
    lText.append('launch_edge = "Falling"')
    return '\n'.join(lText) + '\n'


class TestRoundTripPin(unittest.TestCase):

    def setUp(self):
        oTemporaryDirectory = tempfile.TemporaryDirectory()
        self.addCleanup(oTemporaryDirectory.cleanup)
        sPartFile = os.path.join(oTemporaryDirectory.name, 'part.toml')
        with open(sPartFile, 'w') as oFile:
            oFile.write(build_part_text('SDR-SS-RT'))
        self.oPin = part.create_part(SimpleNamespace(part=sPartFile)).get_pin_named('DOUT')

    def test_round_trip_pin_keeps_its_methodology(self):
        self.assertEqual('SDR-SS-RT', self.oPin.methodology)

    def test_round_trip_pin_keeps_its_launch_edge(self):
        self.assertEqual('Falling', self.oPin.launch_edge)

    def test_round_trip_pin_keeps_its_maximum_clock_to_out(self):
        self.assertEqual(27, self.oPin.cko_max.value)

    def test_round_trip_pin_keeps_its_minimum_clock_to_out(self):
        self.assertEqual(0, self.oPin.cko_min.value)
