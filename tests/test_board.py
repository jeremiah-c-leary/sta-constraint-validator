
import unittest

from stacv import board



dBoardConfig = {}
dBoardConfig['board'] = {}
dBoardConfig['board']['trace'] = {}

dTrace = {}
dTrace['device_pin'] = 'D1'
dTrace['part_pin'] = 'P1'
dTrace['delay'] = {}
dTrace['delay']['max'] = 5.0
dTrace['delay']['min'] = 5.0

dBoardConfig['board']['trace']['first'] = dTrace

dTrace = {}
dTrace['device_pin'] = 'D2'
dTrace['part_pin'] = 'P2'
dTrace['delay'] = {}
dTrace['delay']['max'] = 4.0
dTrace['delay']['min'] = 2.0

dBoardConfig['board']['trace']['second'] = dTrace

dTrace = {}
dTrace['device_pin'] = 'D3'
dTrace['part_pin'] = 'P3'
dTrace['delay'] = {}
dTrace['delay']['max'] = 6.0
dTrace['delay']['min'] = 3.0

dBoardConfig['board']['trace']['third'] = dTrace


class Test(unittest.TestCase):


    def test_new_board(self):
 
        oBoard = board.new(dBoardConfig)

        self.assertEqual(3, len(oBoard.traces))
