'''
One drawing of an edge diagram, and the requirements it shows.
'''

SETUP = 'setup'
HOLD = 'hold'


class EdgeWindow():

    def __init__(self, lLines, lRequirements):
        self.lines = lLines
        self.requirements = lRequirements
