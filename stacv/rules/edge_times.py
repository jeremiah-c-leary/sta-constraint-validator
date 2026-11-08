'''
Contains functions to assist with calculating the time of clock edges.
'''


def calculate_edge_time(fPeriod, iEdgeNumber):
    return (fPeriod / 2) * iEdgeNumber
