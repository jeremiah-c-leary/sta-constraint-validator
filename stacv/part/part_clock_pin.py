class PartClockPin():
    '''
    A clock pin of a part interface: it carries no timing, and the other pins name it as their clock.
    '''

    def __init__(self):
        self.name = None
        self.if_signal = None
