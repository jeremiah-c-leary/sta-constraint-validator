
def new(clock_freq):
    new_clock = clock(clock_freq)
    new_clock.period = calculate_period(clock_freq)

    return new_clock


class clock():
    def __init__(self, clock_freq):
        self.freq = clock_freq
        self.period = None
        self.edges = None


def expand(clock_object, periods):

    clock_object.edges = generate_edges(clock_object.period, periods)


def calculate_period(clock_freq):
    frequency = clock_freq.strip().split()
    if frequency[1].lower() == 'mhz':
        numerator = 1000
    elif frequency[1].lower() == 'khz':
        numerator = 1000000
    period = int(numerator/int(frequency[0]))
    return period


def generate_edges(clock_period, periods):
    edges = []
    for i in range(periods*2 + 1):
        my_edge = edge()
        my_edge.id = calculate_edge_id(i)
        my_edge.direction = calculate_edge_direction(i)
        my_edge.time = calculate_edge_time(i, clock_period)
        edges.append(my_edge)
    return edges


def calculate_edge_id(num):
    return num + 1


def calculate_edge_direction(num):
    if is_rising_edge(num):
        return 'rising'
    else:
        return 'falling'


def is_rising_edge(num):
    if num % 2 == 0:
        return True
    return False


def calculate_edge_time(num, clock_period):
    return num * int(clock_period/2)


class edge():
    def __init__(self):
        self.id = None
        self.edges = None
        self.direction = None
        self.time = None
