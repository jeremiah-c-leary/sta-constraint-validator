'''
Compares the setup and hold checks a designer intended (device YAML) with
the checks the timing tool actually performed (timing reports).

Edge naming follows stacv.clock: edges are counted from 1 at the first
rising edge at or after 0 ns, alternating rising (odd) and falling (even).
Launch edges are numbered, capture edges are lettered (a = 1, b = 2, ...).
'''

import math

from stacv.analysis.report_view import Clock


DIRECTION_WORD = {'rise': 'rising', 'fall': 'falling'}


def index_direction(index):
    return 'rise' if index % 2 == 1 else 'fall'


class Check():
    '''One launch-to-capture relationship.'''

    def __init__(self, kind, launch_time, capture_time, launch_label='', capture_label='',
                 launch_direction=None, capture_direction=None):
        self.kind = kind                    # 'setup' or 'hold'
        self.launch_time = launch_time
        self.capture_time = capture_time
        self.launch_label = launch_label
        self.capture_label = capture_label
        self.launch_direction = launch_direction      # 'rise' or 'fall'
        self.capture_direction = capture_direction

    @property
    def relationship(self):
        return round(self.capture_time - self.launch_time, 3)


class Comparison():

    def __init__(self, pin, intended, reported, launch_clock, capture_clock):
        self.pin = pin
        self.intended = intended            # {'setup': Check, 'hold': Check}
        self.reported = reported
        self.launch_clock = launch_clock
        self.capture_clock = capture_clock

    def differences(self, kind):
        '''
        Ways the reported check departs from the intended one.  The intent is
        the reference: it is never judged, only the report is.
        '''
        intended, reported = self.intended[kind], self.reported[kind]
        found = []
        if reported.relationship != intended.relationship:
            found.append(f'expected {intended.relationship:+.3f} ns')
        for end in ('launch', 'capture'):
            want = getattr(intended, end + '_direction')
            got = getattr(reported, end + '_direction')
            if want and got and want != got:
                verb = {'launch': 'launches', 'capture': 'captures'}[end]
                found.append(f'{verb} on {DIRECTION_WORD[got]} edge, expected {DIRECTION_WORD[want]}')
        return found

    def matches(self, kind):
        return not self.differences(kind)

    def anchored(self, kind):
        '''
        The reported check redrawn from the intended launch edge, where the
        data actually changes: same relationship, so the capture point shows
        where the report expects the capturing edge to be.
        '''
        intended, reported = self.intended[kind], self.reported[kind]
        capture_time = round(intended.launch_time + reported.relationship, 3)
        return Check(kind, intended.launch_time, capture_time,
                     intended.launch_label, edge_name(self.capture_clock, capture_time, numbered=False),
                     reported.launch_direction, reported.capture_direction)

    @property
    def all_match(self):
        return self.matches('setup') and self.matches('hold')


def compare(config, setup_path, hold_path):
    '''
    Returns a Comparison for the endpoint of the given setup and hold paths,
    or None when the device YAML has no intent for that pin.
    '''
    pin = find_device_pin(config, setup_path.destination) or find_device_pin(config, source_port(setup_path))
    if pin is None:
        return None
    name, pin_intent, clocks = pin

    launch_clock = match_clock(clocks, pin_intent['launch_clock']['name'], setup_path.launch_clock)
    capture_clock = match_clock(clocks, pin_intent['capture_clock']['name'], setup_path.capture_clock)
    if launch_clock is None or capture_clock is None:
        return None

    launch_edge = int(pin_intent['launch_clock']['edge'])
    capture_edges = pin_intent['capture_clock']['edge']
    launch_time = edge_time(launch_clock, launch_edge)

    intended = {}
    for kind in ('setup', 'hold'):
        letter = str(capture_edges[kind]).strip().lower()
        capture_index = letter_to_index(letter)
        intended[kind] = Check(kind, launch_time, edge_time(capture_clock, capture_index),
                               f'edge {launch_edge}', letter,
                               index_direction(launch_edge), index_direction(capture_index))

    span = common_period(launch_clock, capture_clock)
    reported = {
        kind: aligned_check(kind, path, intended[kind].launch_time, span)
        for kind, path in (('setup', setup_path), ('hold', hold_path))
    }
    for check in reported.values():
        check.launch_label = edge_name(launch_clock, check.launch_time, numbered=True)
        check.capture_label = edge_name(capture_clock, check.capture_time, numbered=False)

    return Comparison(name, intended, reported, launch_clock, capture_clock)


def source_port(path):
    return path.source.split('/')[0] if path.source else None


def find_device_pin(config, pin_name):
    '''Finds a data pin in the device section. Returns (name, intent, clocks).'''
    if not pin_name or 'device' not in config:
        return None
    for interface in config['device'].get('interface', []):
        for body in interface.values():
            clocks = collect_clocks(body.get('clock', {}))
            for direction in ('output', 'input'):
                for entry in body.get('data', {}).get(direction, []) or []:
                    for name, intent in entry.items():
                        if name == pin_name:
                            return name, intent, clocks
    return None


def collect_clocks(clock_section):
    clocks = {}
    for group in ('internal', 'input', 'output'):
        entries = clock_section.get(group, []) or []
        if isinstance(entries, dict):
            entries = [{k: v} for k, v in entries.items()]
        for entry in entries:
            for name, body in entry.items():
                clocks[name] = body.get('frequency')
    return clocks


def frequency_to_period(text):
    value, unit = text.strip().split()
    scale = {'ghz': 1.0, 'mhz': 1e3, 'khz': 1e6}[unit.lower()]
    return round(scale / float(value), 6)


def match_clock(yaml_clocks, yaml_name, report_clock):
    '''
    Uses the report's waveform for the YAML clock when their periods agree,
    since YAML clock names (pins, internal nets) rarely match SDC clock names.
    '''
    if yaml_name not in yaml_clocks or report_clock is None:
        return None
    period = frequency_to_period(yaml_clocks[yaml_name])
    if abs(period - report_clock.period) > 1e-3:
        return None
    return Clock(f'{yaml_name} ({report_clock.name})', report_clock.rise, report_clock.fall, report_clock.period)


def first_rise(clock):
    return clock.rise % clock.period


def edge_time(clock, index):
    '''Time of the numbered edge (1 = first rising edge at or after 0 ns).'''
    rise = first_rise(clock)
    fall = rise + ((clock.fall - clock.rise) % clock.period)
    cycle = (index - 1) // 2
    base = rise if index % 2 == 1 else fall
    return round(base + cycle * clock.period, 3)


def edge_index(clock, time):
    '''Inverse of edge_time for a time that lands on an edge, otherwise None.'''
    for index in range(1, 400):
        t = edge_time(clock, index)
        if abs(t - time) < 1e-3:
            return index
        if t > time:
            return None
    return None


def letter_to_index(letter):
    return ord(letter) - ord('a') + 1


def edge_name(clock, time, numbered):
    index = edge_index(clock, time)
    if index is None:
        return f'{time:.3f} ns (no edge)'
    if numbered:
        return f'edge {index}'
    return index_to_letters(index)


def index_to_letters(index):
    letters = ''
    while index > 0:
        index, remainder = divmod(index - 1, 26)
        letters = chr(ord('a') + remainder) + letters
    return letters


def common_period(a, b):
    '''Least common multiple of two periods, in ns, at 1 ps resolution.'''
    pa, pb = int(round(a.period * 1000)), int(round(b.period * 1000))
    return pa * pb // math.gcd(pa, pb) / 1000


def aligned_check(kind, path, target_launch, span):
    '''
    Vivado reports edges within its own window of the common period (hold
    edges are normalised to its start).  Shift the reported pair by whole
    common periods only when that brings its launch edge nearer the intended
    launch edge; on a tie the report's own edges are kept, so labels read the
    same as the report text.  Relationship and edge directions are unchanged.
    '''
    launch, capture = path.launch_edge, path.capture_edge
    shift = round((target_launch - launch) / span) * span   # ties round to 0
    return Check(kind, round(launch + shift, 3), round(capture + shift, 3),
                 launch_direction=path.launch_direction,
                 capture_direction=path.capture_direction)
