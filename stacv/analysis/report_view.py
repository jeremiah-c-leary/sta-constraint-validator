'''
Builds a plot-ready view of timing paths directly from a Vivado
report_timing text report.

Each path is split into the pieces a timing diagram needs:

  * launch lane  : launch clock edge -> source clock path -> data path -> arrival
  * capture lane : capture clock edge -> destination clock path
                   -> pessimism / uncertainty / setup, hold or output delay -> required

Every row keeps the cumulative Path(ns) value from the report, so the
diagram is drawn from the tool's own numbers rather than re-derived ones.
'''

import re

ADJUSTMENTS = ('clock pessimism', 'clock uncertainty', 'output delay', 'input delay')

NUMBER = r'-?\d+\.\d+'
ROW_WITH_TIMES = re.compile(r'^(?P<head>.*?)\s+(?P<incr>' + NUMBER + r')\s+(?P<path>' + NUMBER + r')\s*(?P<edge>[rf])?\s*(?P<resource>.*)$')
CLOCK_EDGE = re.compile(r'\(clock (?P<name>\S+) (?P<edge>rise|fall) edge\)')
WAVEFORM = re.compile(r'clocked by (?P<name>\S+)\s+\{(?P<wave>[^}]*)\}')
CORNER = re.compile(r'Path Type:\s+(?P<kind>Max|Min) at (?P<corner>.+)$')
SLACK = re.compile(r'^Slack(?: \((?P<status>[A-Z]+)\))?\s*:\s*(?P<value>' + NUMBER + r')ns')


class Row():
    '''One line of the path table in the report.'''

    def __init__(self, kind, description, incr, path, resource='', location='', fanout=None):
        self.kind = kind              # 'edge', 'cell', 'net' or 'adjust'
        self.description = description
        self.incr = incr
        self.path = path
        self.resource = resource
        self.location = location
        self.fanout = fanout

    @property
    def start(self):
        return round(self.path - self.incr, 3)

    def as_dict(self):
        return {
            'kind': self.kind,
            'description': self.description,
            'incr': self.incr,
            'path': self.path,
            'resource': self.resource,
            'location': self.location,
            'fanout': self.fanout,
        }


class Clock():
    '''A clock as described in the report header, e.g. {rise@0.000ns fall@5.000ns period=10.000ns}.'''

    def __init__(self, name, rise, fall, period):
        self.name = name
        self.rise = rise
        self.fall = fall
        self.period = period

    def level_at(self, time):
        '''Logic level of the ideal clock at the given time.'''
        phase = (time - self.rise) % self.period
        high_time = (self.fall - self.rise) % self.period
        return 1 if phase < high_time else 0


class PathView():

    def __init__(self):
        self.source = None
        self.destination = None
        self.check = None                # 'setup' or 'hold'
        self.corner = None
        self.slack = None
        self.status = None               # 'MET' or 'VIOLATED'
        self.requirement = None
        self.launch_clock = None
        self.capture_clock = None
        self.launch_edge = None
        self.capture_edge = None
        self.launch_direction = None     # 'rise' or 'fall'
        self.capture_direction = None
        self.source_clock_rows = []      # launch edge up to the source register clock pin
        self.data_rows = []              # clock-to-out through to the endpoint
        self.capture_rows = []           # capture edge up to the required time
        self.arrival = None
        self.required = None
        self.file_name = None

    @property
    def launch_rows(self):
        return self.source_clock_rows + self.data_rows

    @property
    def label(self):
        return f'{self.source} to {self.destination}'

    @property
    def met(self):
        return self.slack is not None and self.slack >= 0

    @property
    def output_delay(self):
        '''Output delay constraint value used by the path, or None.'''
        for row in self.capture_rows:
            if row.description.startswith('output delay'):
                return round(-row.incr, 3)
        return None

    @property
    def input_delay(self):
        '''Input delay constraint value used by the path, or None.'''
        for row in self.launch_rows:
            if row.description.startswith('input delay'):
                return round(row.incr, 3)
        return None

    def time_span(self):
        rows = [row for row in self.launch_rows + self.capture_rows if row.kind != 'edge']
        times = [row.path for row in rows] + [row.start for row in rows]
        return min(times), max(times)


def parse(report_lines, file_name=None):
    '''Returns a list of PathView objects, one per path in the report.'''
    paths = []
    for block in split_into_paths(report_lines):
        path = parse_path(block)
        if path is not None:
            path.file_name = file_name
            paths.append(path)
    return paths


def split_into_paths(report_lines):
    blocks = []
    current = None
    for raw in report_lines:
        line = raw.rstrip('\r\n')
        if line.startswith('Slack'):
            current = []
            blocks.append(current)
        if current is not None:
            current.append(line)
    return blocks


def parse_path(lines):
    path = PathView()
    parse_header(lines, path)
    parse_table(lines, path)
    if path.arrival is None or path.required is None:
        return None
    return path


def parse_header(lines, path):
    for index, line in enumerate(lines):
        stripped = line.strip()
        match = SLACK.match(stripped)
        if match:
            path.slack = float(match.group('value'))
            path.status = match.group('status') or ('MET' if path.slack >= 0 else 'VIOLATED')
        elif stripped.startswith('Source:'):
            path.source = stripped.split(':', 1)[1].strip()
            path.launch_clock = clock_from_line(next_line(lines, index))
        elif stripped.startswith('Destination:'):
            path.destination = stripped.split(':', 1)[1].strip()
            path.capture_clock = clock_from_line(next_line(lines, index))
        elif stripped.startswith('Path Type:'):
            match = CORNER.search(stripped)
            if match:
                path.check = 'setup' if match.group('kind') == 'Max' else 'hold'
                path.corner = match.group('corner').strip()
        elif stripped.startswith('Requirement:'):
            path.requirement = first_number(stripped)
        elif 'Location' in stripped and 'Delay type' in stripped:
            break


def next_line(lines, index):
    if index + 1 < len(lines):
        return lines[index + 1]
    return ''


def clock_from_line(line):
    match = WAVEFORM.search(line)
    if not match:
        return None
    wave = match.group('wave')
    rise = float(re.search(r'rise@(' + NUMBER + ')', wave).group(1))
    fall = float(re.search(r'fall@(' + NUMBER + ')', wave).group(1))
    period = float(re.search(r'period=(' + NUMBER + ')', wave).group(1))
    return Clock(match.group('name'), rise, fall, period)


def first_number(text):
    match = re.search(NUMBER, text)
    return float(match.group(0)) if match else None


def parse_table(lines, path):
    '''
    Walks the path table.  Vivado separates the source clock path, the data
    path and the summary with dashed lines, and starts the capture section with
    a second clock edge row.
    '''
    in_table = False
    section = None
    separators = 0
    for index, line in enumerate(lines):
        stripped = line.strip()
        if 'Location' in stripped and 'Delay type' in stripped:
            in_table = True
            continue
        if not in_table:
            continue

        if stripped.startswith('---'):
            separators += 1
            if section == 'source_clock':
                section = 'data'
            elif section == 'data':
                section = 'after_data'
            continue

        edge = CLOCK_EDGE.search(stripped)
        if edge:
            row = build_row(line)
            if row is None:
                # Wider reports wrap the edge label and put its times on the next line.
                row = build_row(line.rstrip() + ' ' + next_line(lines, index).strip())
            if row is None:
                continue
            if path.launch_edge is None:
                path.launch_edge = row.path
                path.launch_direction = edge.group('edge')
                section = 'source_clock'
                path.source_clock_rows.append(row)
            else:
                path.capture_edge = row.path
                path.capture_direction = edge.group('edge')
                section = 'capture'
                path.capture_rows.append(row)
            continue

        if stripped.startswith('required time'):
            path.required = abs(first_number(stripped))
            continue
        if stripped.startswith('arrival time'):
            path.arrival = abs(first_number(stripped))
            continue
        if stripped.startswith('slack'):
            continue

        if index > 0 and CLOCK_EDGE.search(lines[index - 1]) and not ROW_WITH_TIMES.match(lines[index - 1]):
            continue    # times already used by the wrapped clock edge row above
        row = build_row(line)
        if row is None:
            continue
        if section == 'source_clock':
            path.source_clock_rows.append(row)
        elif section == 'data':
            path.data_rows.append(row)
        elif section == 'capture':
            path.capture_rows.append(row)

    # Ports launched directly (for example input delay paths) have no
    # separator between clock and data, so treat everything as data.
    if not path.data_rows and path.source_clock_rows:
        path.data_rows = path.source_clock_rows[1:]
        path.source_clock_rows = path.source_clock_rows[:1]


def build_row(line):
    match = ROW_WITH_TIMES.match(line)
    if not match:
        return None

    head = match.group('head').strip()
    incr = float(match.group('incr'))
    path_time = float(match.group('path'))
    resource = match.group('resource').strip()

    if CLOCK_EDGE.search(head):
        return Row('edge', head, incr, path_time)

    location = ''
    description = head
    if line.startswith('    ') and not line.startswith('                         '):
        parts = head.split(None, 1)
        location = parts[0]
        description = parts[1] if len(parts) > 1 else ''

    if description.startswith('net'):
        fanout = re.search(r'fo=(\d+)', description)
        return Row('net', description, incr, path_time, resource, location,
                   int(fanout.group(1)) if fanout else None)

    if description.startswith(ADJUSTMENTS) or 'Setup_' in description or 'Hold_' in description:
        return Row('adjust', description, incr, path_time, resource, location)

    if not description:
        description = 'port'
    return Row('cell', description, incr, path_time, resource, location)
