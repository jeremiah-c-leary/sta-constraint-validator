from tests.cli import test_part_errors

build_pin = test_part_errors.build_pin
PROPERTIES = test_part_errors.PROPERTIES
DATASHEET = test_part_errors.DATASHEET
INTERFACE = test_part_errors.INTERFACE


class TestPartValues(test_part_errors.PartTestCase):
    '''
    The values of the part file: clock edges, pin names and frequencies.
    '''

    def test_capture_edge_must_be_rising_or_falling(self):
        lReplacements = [('capture_edge', 'capture_edge = "falling"')]
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(lReplacements)], 'part_config_006', 'key "capture_edge" in pin DATA_IN of interface SPI must be "Rising" or "Falling"')

    def test_launch_edge_must_be_rising_or_falling(self):
        lReplacements = []
        lReplacements.append(('methodology', 'methodology = "SDR-SS-RT-DO"'))
        lReplacements.append(('capture_edge', 'launch_edge = "Up"'))
        lReplacements.append(('setup', 'cko_max = {value = 30, symbol = "tCkoMax", source = "Table Z"}'))
        lReplacements.append(('hold', 'cko_min = {value = 0, symbol = "tCkoMin", source = "Table Z"}'))
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(lReplacements)], 'part_config_006', 'key "launch_edge" in pin DATA_IN of interface SPI must be "Rising" or "Falling"')

    def test_pin_defined_twice_is_an_error(self):
        sSecondInterface = '[[interface]]\nname = "SPI_2"'
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(), sSecondInterface, build_pin()], 'part_config_007', 'pin DATA_IN is defined by more than one [[interface.pin]] table')

    def test_max_frequency_must_be_greater_than_zero(self):
        lReplacements = [('clock', 'clock = {pin = "CLK", max_frequency = 0}')]
        self.assert_error([PROPERTIES, DATASHEET, INTERFACE, build_pin(lReplacements)], 'part_config_008', 'key "max_frequency" in clock of pin DATA_IN of interface SPI must be greater than 0')
