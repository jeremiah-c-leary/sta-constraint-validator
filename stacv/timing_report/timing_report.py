
from stacv.timing_report import delay_path
from stacv.timing_report import delay_element


def new(timing_report_struct):

    if is_hold_report(timing_report_struct):
        return build_hold_timing_report(timing_report_struct)


def is_hold_report(timing_report_struct):
    if timing_report_struct['type'] == 'hold':
        return True
    return False


def build_hold_timing_report(timing_report_struct):
    data_path = build_data_path(timing_report_struct)
    required_path = build_required_path(timing_report_struct)
    hold_timing_report = HoldTimingReport(data_path, required_path)
    hold_timing_report.launch_edge = timing_report_struct['launch_edge']
    hold_timing_report.capture_edge = timing_report_struct['capture_edge']
    hold_timing_report.output_delay = timing_report_struct['output_delay']
    hold_timing_report.process_corner = timing_report_struct['process_corner']
    return hold_timing_report


def build_data_path(timing_report_struct):
    return build_path(timing_report_struct['data_path'])


def build_required_path(timing_report_struct):
    return build_path(timing_report_struct['required_path'])


def build_path(path_struct):
    data_path = delay_path.new()
    for path in path_struct:
        data_path.add_delay(delay_element.new(path))
    return data_path


class TimingReport():
    def __init__(self, data_path, required_path):
        self.type = None
        self.data_path = data_path
        self.required_path = required_path
        self.crpr = calculate_crpr(data_path, required_path)


class HoldTimingReport(TimingReport):
    def __init__(self, data_path, required_path):
        TimingReport.__init__(self, data_path, required_path)

    def get_slack(self):
        data_delay = self.launch_edge + self.data_path.total_delay()
        required_delay = self.capture_edge + self.required_path.total_delay() - self.crpr - self.output_delay
        slack = round(data_delay - required_delay, 3)
        return slack


def calculate_crpr(data_path, required_path):
    crpr = 0
    for data, required in zip(data_path.delays, required_path.delays):
        if resources_match(data, required):
            delta = abs(data.delay - required.delay)
            crpr += delta
        else:
            crpr -= delta
            break

    return crpr


def resources_match(data, required):
    if data.resource == required.resource:
        return True
    return False
