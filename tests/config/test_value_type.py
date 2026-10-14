import unittest

from stacv.config import value_type


class TestArrayOfTablesType(unittest.TestCase):

    def test_description(self):
        self.assertEqual('an array of tables', value_type.ARRAY_OF_TABLES.description)

    def test_is_valid_accepts_list_of_tables(self):
        self.assertTrue(value_type.ARRAY_OF_TABLES.is_valid([{'name': 'DAC_SPI_1'}, {'name': 'DAC_SPI_2'}]))

    def test_is_valid_accepts_empty_list(self):
        self.assertTrue(value_type.ARRAY_OF_TABLES.is_valid([]))

    def test_is_valid_rejects_string(self):
        self.assertFalse(value_type.ARRAY_OF_TABLES.is_valid('DAC_SPI_1'))

    def test_is_valid_rejects_number(self):
        self.assertFalse(value_type.ARRAY_OF_TABLES.is_valid(5))

    def test_is_valid_rejects_single_table(self):
        self.assertFalse(value_type.ARRAY_OF_TABLES.is_valid({'name': 'DAC_SPI_1'}))

    def test_is_valid_rejects_list_of_strings(self):
        self.assertFalse(value_type.ARRAY_OF_TABLES.is_valid(['DAC_SPI_1', 'DAC_SPI_2']))

    def test_is_valid_rejects_list_with_a_string_after_a_table(self):
        self.assertFalse(value_type.ARRAY_OF_TABLES.is_valid([{'name': 'DAC_SPI_1'}, 'DAC_SPI_2']))
