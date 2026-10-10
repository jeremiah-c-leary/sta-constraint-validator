
class DelayPath():
    def __init__(self, oLine):
        self.first_line = oLine
        self.delays = []

    def add_delay(self, delay):
        self.delays.append(delay)

    def total_delay(self):
        my_total = 0.000
        for my_delay in self.delays:
            my_total += my_delay.delay
            my_total = round(my_total, 3)
        return my_total

    def get_resources(self):
        lResources = []
        for oDelay in self.delays:
            lResources.append(oDelay.resource)
        return lResources
