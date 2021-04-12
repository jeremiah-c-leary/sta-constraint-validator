
def new(data_path, required_path):

    return HoldTimingReport(data_path, required_path)


class TimingReport():
    def __init__(self, data_path, required_path):
        self.type = None
        self.data_path = data_path
        self.required_path = required_path
        self.crpr = calculate_crpr(data_path, required_path)


def calculate_crpr(data_path, required_path):
    crpr = 0
    for data, required in zip(data_path.delays, required_path.delays):
        if has_matching_resource(data, required):
            delta = abs(data.delay - required.delay)
            crpr += delta
        else:
            crpr -= delta
            break

    return crpr


def has_matching_resource(data, required):
    if data.resource == required.resource:
        return True
    return False

    
class HoldTimingReport(TimingReport):
    def __init__(self, data_path, required_path):
        TimingReport.__init__(self, data_path, required_path)

    def get_slack(self):
        data_delay = self.launch_edge + self.data_path.total_delay()
        required_delay = self.capture_edge + self.required_path.total_delay() - self.crpr - self.output_delay
        slack = data_delay - required_delay 
        return slack
