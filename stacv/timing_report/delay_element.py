
def new(delay_dict):

    if is_cell_delay(delay_dict):
        return build_cell_delay(delay_dict)
    elif is_net_delay(delay_dict):
        return build_net_delay(delay_dict)


def is_cell_delay(delay_dict):
    if delay_dict['type'] == 'cell':
        return True
    return False


def is_net_delay(delay_dict):
    if delay_dict['type'] == 'net':
        return True
    return False


def build_cell_delay(delay_dict):

    my_delay = CellDelay()
    my_delay.location = delay_dict['location']
    my_delay.delay_type = delay_dict['delay_type']
    my_delay.delay = delay_dict['delay']
    my_delay.resource = delay_dict['resource']
    return my_delay


def build_net_delay(delay_dict):

    my_delay = NetDelay()
    my_delay.delay = delay_dict['delay']
    my_delay.resource = delay_dict['resource']
    my_delay.fan_out = delay_dict['fan_out']
    return my_delay


class Delay():
    def __init__(self):
        self.delay = None
        self.resource = None


class CellDelay(Delay):
    def __init__(self):
        Delay.__init__(self)
        self.location = None
        self.delay_type = None


class NetDelay(Delay):
    def __init__(self):
        Delay.__init__(self)
        self.fan_out = None
