'''
Contains functions to assist with calculating the time of clock edges.
'''


LETTERS = 26


def convert_edge_letter_to_number(sEdgeLetter):
    # Capture edges count A to Z, then AA, AB, ... as spreadsheet columns do, with A as edge 0.
    iNumber = 0
    for sLetter in sEdgeLetter:
        iNumber = iNumber * LETTERS + ord(sLetter) - ord('A') + 1
    return iNumber - 1


def convert_edge_number_to_letter(iEdgeNumber):
    sLetters = ''
    iRemaining = iEdgeNumber + 1
    while iRemaining > 0:
        iRemaining, iLetter = divmod(iRemaining - 1, LETTERS)
        sLetters = chr(ord('A') + iLetter) + sLetters
    return sLetters


def calculate_edge_time(fPeriod, iEdgeNumber):
    return (fPeriod / 2) * iEdgeNumber


def calculate_clock_edge_time(oClock, iEdgeNumber):
    # The edge's time, shifted by the clock's phase.
    return calculate_edge_time(oClock.period, iEdgeNumber) + oClock.phase
