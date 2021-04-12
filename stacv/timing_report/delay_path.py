
def new():

    return DelayPath()


class DelayPath():
    def __init__(self):
        self.delays = []

    def add_delay(self, delay):
        self.delays.append(delay)

    def total_delay(self):
        my_total = 0.000
        for my_delay in self.delays:
            my_total += my_delay.delay
            my_total = round(my_total, 3)
        return my_total
