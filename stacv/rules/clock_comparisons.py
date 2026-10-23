'''
Contains functions to assist with clock rules.
'''

def clock_period_is_within_tolerance(fExpected, fActual, fTolerance):
    return fExpected - fTolerance < fActual < fExpected + fTolerance



