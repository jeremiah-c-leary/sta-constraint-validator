'''
Contains functions to assist with comparing values within a tolerance.
'''


def is_within_tolerance(fExpected, fActual, fTolerance):
    return fExpected - fTolerance < fActual < fExpected + fTolerance
