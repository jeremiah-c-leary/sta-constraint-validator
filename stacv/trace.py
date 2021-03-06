
class New():

    def __init__(self, trace_dict):
        self.name = list(trace_dict.keys())[0]
        self.device_pin = trace_dict[self.name]['device_pin']
        self.part_pin = trace_dict[self.name]['part_pin']
        self.min_delay = trace_dict[self.name]['delay']['min']
        self.max_delay = trace_dict[self.name]['delay']['max']

    @property
    def min_delay(self):
        return self.__min_delay

    @min_delay.setter
    def min_delay(self, min_delay):
        if min_delay < 0:
            raise ValueError(f'Trace {self.name} Min delay value must be greater than 0.')
        else:
            self.__min_delay = min_delay

    @property
    def max_delay(self):
        return self.__max_delay

    @max_delay.setter
    def max_delay(self, max_delay):
        if max_delay < self.__min_delay:
            raise ValueError(f'Trace {self.name} Max delay value must be greater than Min delay value.')
        else:
            self.__max_delay = max_delay
