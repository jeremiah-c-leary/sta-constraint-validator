'''
Contains functions to assist with calculating the time of clock edges.
'''


def convert_edge_letter_to_number(sEdgeLetter):
    return ord(sEdgeLetter) - ord('A')


def calculate_edge_time(fPeriod, iEdgeNumber):
    return (fPeriod / 2) * iEdgeNumber
