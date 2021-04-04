
import unittest

from stacv import board



dBoardConfig = {}
dBoardConfig['board'] = {}
dBoardConfig['board']['trace'] = []

dTrace = {}
dTrace['first'] = {}
dTrace['first']['device_pin'] = 'D1'
dTrace['first']['part_pin'] = 'P1'
dTrace['first']['delay'] = {}
dTrace['first']['delay']['max'] = 5.0
dTrace['first']['delay']['min'] = 5.0

dBoardConfig['board']['trace'].append(dTrace)

dTrace = {}
dTrace['second'] = {}
dTrace['second']['device_pin'] = 'D2'
dTrace['second']['part_pin'] = 'P2'
dTrace['second']['delay'] = {}
dTrace['second']['delay']['max'] = 4.0
dTrace['second']['delay']['min'] = 2.0

dBoardConfig['board']['trace'].append(dTrace)

dTrace = {}
dTrace['third'] = {}
dTrace['third']['device_pin'] = 'D3'
dTrace['third']['part_pin'] = 'P3'
dTrace['third']['delay'] = {}
dTrace['third']['delay']['max'] = 6.0
dTrace['third']['delay']['min'] = 3.0

dBoardConfig['board']['trace'].append(dTrace)


class Test(unittest.TestCase):


    def test_new_board(self):
 
        oBoard = board.new(dBoardConfig)

        self.assertEqual(3, len(oBoard.traces))
