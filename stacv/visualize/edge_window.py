'''
One drawing of an edge diagram, and the requirements it shows.
'''

SETUP = 'setup'
HOLD = 'hold'


class EdgeWindow():

    def __init__(self, lLines, lRequirements):
        self.lines = lLines
        self.requirements = lRequirements


def join_windows(lWindows, dRequirementLines, sBlankLine):
    # Each window is followed by the lines of the requirements it shows, with a blank line around them.
    lLines = []
    for iIndex, oWindow in enumerate(lWindows):
        if iIndex > 0:
            lLines.append(sBlankLine)
        lLines.extend(oWindow.lines)
        lLines.append(sBlankLine)
        for sRequirement in oWindow.requirements:
            lLines.append(dRequirementLines[sRequirement])
    return lLines
