'''
Staged validation of an interface's timing reports against its intent.

Checks run in dependency order.  A check whose prerequisites did not pass
is skipped rather than failed, so each failure points at the first thing
that is actually wrong, and slack is only judged once the constraints that
produce it have been shown to match the intent.

The intent (device, part and board YAML) is the reference.  Every failure
describes what the timing report did compared with what was intended.
'''

from stacv.analysis import intent, registry, report_view

PASS, FAIL, SKIP = 'pass', 'fail', 'skip'

STAGES = registry.STAGES
DEFAULT_CORNERS = ('Slow', 'Fast')
TOLERANCE = 0.001


class Result():

    def __init__(self, definition):
        self.definition = definition
        self.status = None
        self.message = ''
        self.details = []            # extra lines for the review report

    @property
    def check_id(self):
        return self.definition.check_id

    @property
    def stage(self):
        return self.definition.stage

    @property
    def title(self):
        return self.definition.title

    @property
    def requires(self):
        return self.definition.requires

    def set(self, status, message, details=None):
        self.status = status
        self.message = message
        self.details = details or []
        return self


class PinValidation():
    '''All checks for one interface data pin.'''

    def __init__(self, interface, pin, direction):
        self.interface = interface
        self.pin = pin
        self.direction = direction          # 'output' or 'input'
        self.results = []
        self.setup_paths = []
        self.hold_paths = []
        self.comparisons = []

    @property
    def name(self):
        return f'{self.interface}.{self.pin}'

    def result(self, check_id):
        for result in self.results:
            if result.check_id == check_id:
                return result
        return None

    def count(self, status):
        return sum(1 for r in self.results if r.status == status)

    @property
    def status(self):
        if self.count(FAIL):
            return FAIL
        if self.count(SKIP):
            return SKIP
        return PASS


def validate(config, report_paths, corners=DEFAULT_CORNERS):
    '''Runs every check for every data pin in the device section.'''
    return [validate_pin(config, interface, pin, direction, report_paths, corners)
            for interface, pin, direction in device_data_pins(config)]


def load_reports(file_names):
    paths = []
    for file_name in file_names:
        with open(file_name, encoding='utf-8', errors='replace') as handle:
            paths.extend(report_view.parse(handle.readlines(), file_name))
    return paths


def device_data_pins(config):
    for entry in config.get('device', {}).get('interface', []) or []:
        for interface, body in entry.items():
            for direction in ('output', 'input'):
                for pin_entry in body.get('data', {}).get(direction, []) or []:
                    for pin in pin_entry:
                        yield interface, pin, direction


def paths_for_pin(report_paths, pin, direction):
    if direction == 'output':
        return [p for p in report_paths if p.destination == pin]
    return [p for p in report_paths if p.source == pin]


def runners(config, corners):
    return {
        'INT-001': lambda v, r: check_connections(config, v, r),
        'INT-002': lambda v, r: check_clocks_defined(config, v, r),
        'INT-003': lambda v, r: check_edge_agreement(config, v, r),
        'COV-001': check_reports_present,
        'COV-002': lambda v, r: check_corners(v, r, corners),
        'STR-001': check_common_source,
        'STR-002': lambda v, r: check_clock_pin(config, v, r),
        'STR-003': check_data_pin,
        'STR-004': check_same_clock_paths,
        'STR-005': check_crpr,
        'EDG-001': lambda v, r: check_edges(config, v, r, 'setup'),
        'EDG-002': lambda v, r: check_edges(config, v, r, 'hold'),
        'DLY-001': lambda v, r: check_delay(config, v, r, 'max'),
        'DLY-002': lambda v, r: check_delay(config, v, r, 'min'),
        'SLK-001': lambda v, r: check_slack(v, r, 'setup'),
        'SLK-002': lambda v, r: check_slack(v, r, 'hold'),
    }


def run_order():
    '''Registry order, adjusted so every check runs after its dependencies.'''
    done, order = set(), []
    pending = list(registry.CHECKS)
    while pending:
        for definition in pending:
            if all(dep in done for dep in definition.requires):
                order.append(definition)
                done.add(definition.check_id)
                pending.remove(definition)
                break
        else:
            raise ValueError('Circular check dependencies in the registry.')
    return order


def validate_pin(config, interface, pin, direction, report_paths, corners):
    validation = PinValidation(interface, pin, direction)
    paths = paths_for_pin(report_paths, pin, direction)
    validation.setup_paths = [p for p in paths if p.check == 'setup']
    validation.hold_paths = [p for p in paths if p.check == 'hold']

    run = runners(config, corners)
    by_id = {}
    for definition in run_order():
        result = Result(definition)
        by_id[definition.check_id] = result
        blocked = [by_id[dep] for dep in definition.requires if by_id[dep].status != PASS]
        if blocked:
            result.set(SKIP, 'Not checked until these pass: ' + ', '.join(b.check_id for b in blocked) + '.')
        else:
            run[definition.check_id](validation, result)
    validation.results = [by_id[d.check_id] for d in registry.CHECKS]
    return validation


# Intent consistency

def pin_intent(config, validation):
    found = intent.find_device_pin(config, validation.pin)
    return found[1] if found else None


def interface_clock_pin(pin_intent_dict, direction):
    side = 'capture_clock' if direction == 'output' else 'launch_clock'
    return pin_intent_dict[side]['name']


def check_connections(config, validation, result):
    found = intent.find_device_pin(config, validation.pin)
    _, intent_dict, clocks = found
    clock_pin = interface_clock_pin(intent_dict, validation.direction)
    problems, details = [], []
    for device_pin in (validation.pin, clock_pin):
        trace = board_trace(config, device_pin)
        if trace is None:
            if device_pin == clock_pin and clock_pin not in device_output_or_input_clocks(config, validation.pin):
                problems.append(f'{device_pin} is an internal clock, not an interface clock pin')
            else:
                problems.append(f'no board trace from {device_pin}')
            continue
        if not part_has_pin(config, trace['part_pin']):
            problems.append(f'trace from {device_pin} goes to {trace["part_pin"]}, which the part does not define')
            continue
        details.append(f'{device_pin} to {trace["part_pin"]}')
    if problems:
        return result.set(FAIL, '; '.join(problems).capitalize() + '.', details)
    return result.set(PASS, 'Connected: ' + ', '.join(details) + '.')


def device_output_or_input_clocks(config, pin):
    names = set()
    for entry in config.get('device', {}).get('interface', []) or []:
        for body in entry.values():
            for group in ('input', 'output'):
                items = body.get('clock', {}).get(group, []) or []
                if isinstance(items, dict):
                    items = [{k: v} for k, v in items.items()]
                for item in items:
                    names.update(item.keys())
    return names


def check_clocks_defined(config, validation, result):
    _, intent_dict, clocks = intent.find_device_pin(config, validation.pin)
    problems = []
    for side in ('launch_clock', 'capture_clock'):
        name = intent_dict.get(side, {}).get('name')
        if name not in clocks:
            problems.append(f'{side.replace("_", " ")} {name} is not defined')
        elif not clocks[name]:
            problems.append(f'{side.replace("_", " ")} {name} has no frequency')
        else:
            try:
                intent.frequency_to_period(clocks[name])
            except (ValueError, KeyError):
                problems.append(f'{side.replace("_", " ")} {name} frequency "{clocks[name]}" is not understood')
    if problems:
        return result.set(FAIL, '; '.join(problems).capitalize() + '.')
    names = [intent_dict[s]['name'] for s in ('launch_clock', 'capture_clock')]
    return result.set(PASS, 'Clocks defined: ' + ', '.join(f'{n} ({clocks[n]})' for n in names) + '.')


def check_edge_agreement(config, validation, result):
    intent_dict = pin_intent(config, validation)
    trace = board_trace(config, validation.pin)
    part_pin = part_data_pin(config, trace['part_pin'])
    part_edges = [k for k in (part_pin or {}) if k in ('rising', 'falling')]
    if not part_edges:
        return result.set(SKIP, f'The part does not give an edge for {trace["part_pin"]}.')
    part_edge = part_edges[0]

    if validation.direction == 'output':
        edges = intent_dict['capture_clock']['edge']
        used = {kind: 'rising' if intent.letter_to_index(str(edges[kind]).lower()) % 2 else 'falling'
                for kind in ('setup', 'hold')}
        where = 'captures'
    else:
        edge = int(intent_dict['launch_clock']['edge'])
        used = {'launch': 'rising' if edge % 2 else 'falling'}
        where = 'launches'
    disagree = [f'{kind} uses the {edge} edge' for kind, edge in used.items() if edge != part_edge]
    if disagree:
        return result.set(FAIL, f'The part datasheet {where} {trace["part_pin"]} on the {part_edge} edge, '
                                f'but the device intent {", ".join(disagree)}.')
    return result.set(PASS, f'Both use the {part_edge} edge of the interface clock.')


# Path structure

def clock_resources(rows):
    '''Physical elements of a clock path, ignoring edge and adjustment rows.'''
    return [row.resource for row in rows if row.kind in ('cell', 'net') and row.resource]


def check_common_source(validation, result):
    details, problems = [], []
    for path in validation.setup_paths + validation.hold_paths:
        launch = clock_resources(path.source_clock_rows)
        capture = clock_resources(path.capture_rows)
        if not launch or not capture:
            problems.append(f'{path.check} at {path.corner}: clock path not reported')
            continue
        details.append(f'{path.check} at {path.corner}: launch from {launch[0]}, capture from {capture[0]}')
        if launch[0] != capture[0]:
            problems.append(f'{path.check} at {path.corner}: launch clock starts at {launch[0]}, '
                            f'capture clock at {capture[0]}')
    if problems:
        return result.set(FAIL, '; '.join(problems) + '.', details)
    return result.set(PASS, f'Both clock paths start at {launch[0]}.', details)


def check_clock_pin(config, validation, result):
    clock_pin = interface_clock_pin(pin_intent(config, validation), validation.direction)
    if validation.direction == 'input':
        rows_of = lambda path: path.source_clock_rows
        side = 'launch'
    else:
        rows_of = lambda path: path.capture_rows
        side = 'capture'
    problems = []
    for path in validation.setup_paths + validation.hold_paths:
        resources = clock_resources(rows_of(path))
        if not any(r == clock_pin or r.startswith(clock_pin + ' ') for r in resources):
            end = resources[-1] if resources else 'nothing'
            problems.append(f'{path.check} at {path.corner}: {side} clock path ends at {end}')
    if problems:
        return result.set(FAIL, f'Expected the {side} clock path to reach {clock_pin}; ' + '; '.join(problems) + '.')
    return result.set(PASS, f'The {side} clock path reaches {clock_pin}.')


def check_data_pin(validation, result):
    problems = []
    for path in validation.setup_paths + validation.hold_paths:
        resources = [row.resource.split()[0] for row in path.data_rows if row.resource]
        endpoint = (resources[-1] if validation.direction == 'output' else
                    (clock_resources(path.data_rows) or [''])[0].split()[0]) if resources else ''
        if endpoint != validation.pin:
            problems.append(f'{path.check} at {path.corner}: data path ends at {endpoint or "nothing"}')
    if problems:
        return result.set(FAIL, f'Expected the data path to reach {validation.pin}; ' + '; '.join(problems) + '.')
    return result.set(PASS, f'The data path reaches {validation.pin}.')


def check_same_clock_paths(validation, result):
    problems = []
    for setup, hold in pairs(validation):
        for name, rows_of in (('launch', lambda p: p.source_clock_rows), ('capture', lambda p: p.capture_rows)):
            a, b = clock_resources(rows_of(setup)), clock_resources(rows_of(hold))
            if a != b:
                where = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
                got_a = a[where] if where < len(a) else 'end of path'
                got_b = b[where] if where < len(b) else 'end of path'
                problems.append(f'{name} clock paths differ at element {where + 1}: '
                                f'setup uses {got_a}, hold uses {got_b}')
    if problems:
        return result.set(FAIL, '; '.join(problems) + '.')
    return result.set(PASS, 'Setup and hold use the same launch and capture clock paths.')


def expected_crpr(path):
    '''
    Pessimism on the shared part of the launch and capture clock paths: the
    delay difference of each common element up to the point of divergence.
    The last common net fans out to both branches, so it is not shared delay.
    '''
    launch = [r for r in path.launch_rows if r.kind in ('cell', 'net') and r.resource]
    capture = [r for r in path.capture_rows if r.kind in ('cell', 'net') and r.resource]
    common = []
    for a, b in zip(launch, capture):
        if a.resource != b.resource:
            break
        common.append((a, b))
    if common and common[-1][0].kind == 'net':
        common = common[:-1]
    return round(sum(abs(a.incr - b.incr) for a, b in common), 3), common


def reported_crpr(path):
    for row in path.capture_rows:
        if row.description.startswith('clock pessimism'):
            return round(abs(row.incr), 3)
    return 0.0


def check_crpr(validation, result):
    problems, details = [], []
    for path in validation.setup_paths + validation.hold_paths:
        expected, common = expected_crpr(path)
        used = reported_crpr(path)
        point = common[-1][0].resource if common else 'no common element'
        details.append(f'{path.check} at {path.corner}: common point {point}, '
                       f'expected {expected:.3f} ns, report removes {used:.3f} ns')
        # Each printed delay is rounded to 1 ps, so every difference summed
        # can be off by up to 1 ps against Vivado's unrounded calculation.
        tolerance = TOLERANCE * max(1, sum(1 for a, b in common if a.incr or b.incr)) + 1e-9
        if abs(expected - used) > tolerance:
            problems.append(f'{path.check} at {path.corner}: report removes {used:.3f} ns, '
                            f'expected {expected:.3f} ns from the common point {point}')
    if problems:
        return result.set(FAIL, '; '.join(problems) + '.', details)
    return result.set(PASS, f'Pessimism removed at {point}.', details)


def part_has_pin(config, part_pin):
    for entry in config.get('part', {}).get('interface', []) or []:
        for body in entry.values():
            for section in ('clock', 'data'):
                groups = body.get(section, {}) or {}
                for direction in ('input', 'output'):
                    for item in groups.get(direction, []) or []:
                        if part_pin in item:
                            return True
    return False


def check_reports_present(validation, result):
    missing = [kind for kind, paths in (('setup', validation.setup_paths), ('hold', validation.hold_paths))
               if not paths]
    if missing:
        return result.set(FAIL, f'No {" or ".join(missing)} report found for {validation.pin}.')
    return result.set(PASS, f'{len(validation.setup_paths)} setup and {len(validation.hold_paths)} hold paths.')


def check_corners(validation, result, corners):
    details, missing = [], []
    for kind, paths in (('setup', validation.setup_paths), ('hold', validation.hold_paths)):
        found = sorted({p.corner for p in paths})
        details.append(f'{kind}: {", ".join(found)}')
        for corner in corners:
            if not any(corner.lower() in (c or '').lower() for c in found):
                missing.append(f'{kind} at {corner}')
    if missing:
        return result.set(FAIL, f'Missing {", ".join(missing)} corner.', details)
    return result.set(PASS, 'All required corners reported.', details)


def pairs(validation):
    '''Setup and hold paths paired by corner.'''
    for setup in validation.setup_paths:
        same = [h for h in validation.hold_paths if h.corner == setup.corner]
        yield setup, (same or validation.hold_paths)[0]


def check_edges(config, validation, result, kind):
    failures, details = [], []
    for setup, hold in pairs(validation):
        comparison = intent.compare(config, setup, hold)
        if comparison is None:
            return result.set(FAIL, f'Report clocks do not match the clocks in the intent for {validation.pin}.')
        if kind == 'setup':
            validation.comparisons.append(comparison)
        want, got = comparison.intended[kind], comparison.reported[kind]
        line = (f'{setup.corner}: intended {want.launch_label} to {want.capture_label} '
                f'({want.relationship:+.3f} ns), report {got.launch_label} to {got.capture_label} '
                f'({got.relationship:+.3f} ns)')
        details.append(line)
        differences = comparison.differences(kind)
        if differences:
            anchored = comparison.anchored(kind)
            from_launch = ''
            if 'no edge' in anchored.capture_label:
                from_launch = (f'; from {want.launch_label}, where the data changes, this captures at '
                               f'{anchored.capture_time:.3f} ns, where {comparison.capture_clock.name.split(" ")[0]} '
                               f'has no edge')
            failures.append(f'{setup.corner}: report checks {got.launch_label} to {got.capture_label} '
                            f'({got.relationship:+.3f} ns), intended {want.launch_label} to '
                            f'{want.capture_label} ({want.relationship:+.3f} ns)'
                            + ''.join(f', {d}' for d in differences if not d.startswith('expected'))
                            + from_launch)
    if failures:
        return result.set(FAIL, '; '.join(failures) + '.')
    return result.set(PASS, f'Report checks {want.launch_label} to {want.capture_label}.', details)


def check_delay(config, validation, result, bound):
    derived = derive_delay(config, validation.pin, validation.direction)
    if derived is None:
        return result.set(SKIP, 'No datasheet or board values in the intent for this pin.')
    expected, formula = derived[bound]

    paths = validation.setup_paths if bound == 'max' else validation.hold_paths
    word = 'output' if validation.direction == 'output' else 'input'
    failures, details = [], [formula]
    for path in paths:
        used = path.output_delay if validation.direction == 'output' else path.input_delay
        if used is None:
            failures.append(f'{path.corner}: no {word} delay in the {path.check} report')
            continue
        details.append(f'{path.corner} {path.check} report uses {used:.3f} ns')
        if abs(used - expected) > TOLERANCE:
            failures.append(f'{path.corner}: report uses {used:.3f} ns, expected {expected:.3f} ns')
    if failures:
        return result.set(FAIL, '; '.join(failures) + '.', details)
    return result.set(PASS, f'Report uses {expected:.3f} ns.', details)


def derive_delay(config, pin, direction):
    '''
    Output delay (source synchronous, forwarded clock):
        max =  tsu + data_trace_max - clock_trace_min
        min = -th  + data_trace_min - clock_trace_max
    Input delay (round trip through the part):
        max = clock_trace_max + tco_max + data_trace_max
        min = clock_trace_min + tco_min + data_trace_min
    '''
    found = intent.find_device_pin(config, pin)
    if found is None:
        return None
    _, pin_intent, _ = found
    clock_pin = (pin_intent.get('capture_clock') if direction == 'output'
                 else pin_intent.get('launch_clock'))['name']

    data_trace = board_trace(config, pin)
    clock_trace = board_trace(config, clock_pin)
    if data_trace is None or clock_trace is None:
        return None
    part_pin = part_data_pin(config, data_trace['part_pin'])
    if part_pin is None:
        return None
    timing = next((v for k, v in part_pin.items() if k in ('rising', 'falling')), None)
    if timing is None:
        return None

    d_max, d_min = float(data_trace['delay']['max']), float(data_trace['delay']['min'])
    c_max, c_min = float(clock_trace['delay']['max']), float(clock_trace['delay']['min'])

    if direction == 'output':
        tsu, th = timing['setup'], timing['hold']
        su, ho = float(tsu['value']), float(th['value'])
        return {
            'max': (round(su + d_max - c_min, 3),
                    f'max = {tsu["id"]} + data trace max - clock trace min = '
                    f'{su:.3f} + {d_max:.3f} - {c_min:.3f} = {su + d_max - c_min:.3f} ns'),
            'min': (round(-ho + d_min - c_max, 3),
                    f'min = -{th["id"]} + data trace min - clock trace max = '
                    f'-{ho:.3f} + {d_min:.3f} - {c_max:.3f} = {-ho + d_min - c_max:.3f} ns'),
        }

    tco_max, tco_min = timing['clock_to_out_max'], timing['clock_to_out_min']
    hi, lo = float(tco_max['value']), float(tco_min['value'])
    return {
        'max': (round(c_max + hi + d_max, 3),
                f'max = clock trace max + {tco_max["id"]} max + data trace max = '
                f'{c_max:.3f} + {hi:.3f} + {d_max:.3f} = {c_max + hi + d_max:.3f} ns'),
        'min': (round(c_min + lo + d_min, 3),
                f'min = clock trace min + {tco_min["id"]} min + data trace min = '
                f'{c_min:.3f} + {lo:.3f} + {d_min:.3f} = {c_min + lo + d_min:.3f} ns'),
    }


def board_trace(config, device_pin):
    for entry in config.get('board', {}).get('trace', []) or []:
        for body in entry.values():
            if body.get('device_pin') == device_pin:
                return body
    return None


def part_data_pin(config, part_pin):
    for entry in config.get('part', {}).get('interface', []) or []:
        for body in entry.values():
            for direction in ('input', 'output'):
                for pin_entry in body.get('data', {}).get(direction, []) or []:
                    if part_pin in pin_entry:
                        return pin_entry[part_pin]
    return None


def check_slack(validation, result, kind):
    paths = validation.setup_paths if kind == 'setup' else validation.hold_paths
    worst = min(paths, key=lambda p: p.slack)
    details = [f'{p.corner}: {p.slack:+.3f} ns' for p in paths]
    if worst.slack < 0:
        return result.set(FAIL, f'Worst {kind} slack {worst.slack:.3f} ns at {worst.corner}.', details)
    return result.set(PASS, f'Worst {kind} slack {worst.slack:.3f} ns at {worst.corner}.', details)
