
class PortResult():

    def __init__(self, oPort, oMethodologyResults):
        self.port = oPort
        self.methodology_results = oMethodologyResults
        # The worst slack of the port's setup and hold paths, in ns, or None when its reports have no such paths.
        self.setup_slack = None
        self.hold_slack = None

    def describe_slack(self):
        # The slack is only shown for a port that passed, as a failing rule can mean the timing tool's slack is wrong.
        lParts = []
        if self.setup_slack is not None:
            lParts.append(f'setup slack {format_slack(self.setup_slack)}')
        if self.hold_slack is not None:
            lParts.append(f'hold slack {format_slack(self.hold_slack)}')
        return ', '.join(lParts)

    def get_identifier(self):
        return self.port.name + '.' + self.port.methodology

    def get_number_of_failures(self):
        return self.get_results().get_number_of_failures()

    def get_number_of_rules(self):
        return self.get_results().get_number_of_rules()

    def get_number_of_skips(self):
        return self.get_results().get_number_of_skips()

    def get_results(self):
        return self.methodology_results.get_results()

    def has_failures(self):
        return self.methodology_results.has_failures()

    def is_deferred(self):
        return False


def format_slack(fSlack):
    return f'{fSlack:.3f} ns'
