'''
Registry of every check stacv performs.

Each check has a permanent identifier: a stage prefix and a number.
Numbers are never reused or renumbered; a retired check keeps its number.
Titles and descriptions may be reworded without changing the identifier.
Run order comes from the dependencies, not from the numbering.

The registry is the single source for the JUnit output, the review report
and the documentation page, so they cannot drift apart.
'''


class CheckDefinition():

    def __init__(self, check_id, title, description, did=None, requires=()):
        self.check_id = check_id
        self.title = title
        self.description = description
        self.did = did
        self.requires = list(requires)

    @property
    def stage(self):
        return self.check_id.split('-')[0]


STAGES = [
    ('INT', 'Intent consistency'),
    ('COV', 'Coverage'),
    ('STR', 'Path structure'),
    ('EDG', 'Launch and capture edges'),
    ('DLY', 'Input and output delays'),
    ('SLK', 'Slack'),
]

STRUCTURE = ['STR-001', 'STR-002', 'STR-003', 'STR-004', 'STR-005']

CHECKS = [
    CheckDefinition(
        'INT-001', 'Each device data pin connects to a part pin through a board trace',
        'The board section must contain a trace from the device data pin, and from the pin\'s '
        'interface clock, to pins that exist in the part section. Without these the input and '
        'output delays cannot be derived.'),
    CheckDefinition(
        'INT-002', 'Each clock referenced by a pin is defined with a frequency',
        'The launch and capture clocks named for the pin must be defined in the device section '
        'with a frequency, so the numbered and lettered edges can be resolved to times and '
        'matched to the clocks in the timing report.'),
    CheckDefinition(
        'INT-003', 'Device capture edge direction agrees with the part datasheet',
        'The device and part intent files are compared with each other: the clock edge direction '
        'the device intent uses at the part must be the edge the part datasheet specifies. This '
        'does not judge which file is correct, only that they disagree.',
        requires=['INT-001']),
    CheckDefinition(
        'COV-001', 'Setup and hold reports present for each pin',
        'At least one setup (max) and one hold (min) path must be reported for the pin. Every '
        'later check is based on these paths.',
        requires=['INT-001', 'INT-002']),
    CheckDefinition(
        'COV-002', 'Required process corners reported',
        'Setup and hold paths must be reported at every required process corner (by default the '
        'slow and fast corners). Slack at one corner says nothing about the others.',
        did='3.x.3.1 h', requires=['COV-001']),
    CheckDefinition(
        'STR-001', 'Data and clock paths share a common source',
        'The clock path that launches the data and the clock path that captures it must start '
        'from the same clock source. Otherwise the relationship between them is not defined by '
        'the design and the analysis is not meaningful.',
        did='3.x.3.1 a', requires=['COV-001']),
    CheckDefinition(
        'STR-002', 'Clock path traces to the external clock pin',
        'For forwarded clocks the capture clock path must reach the device pin of the interface '
        'clock. A capture clock defined elsewhere means the report is not timing the clock the '
        'part actually receives.',
        did='3.x.3.1 c', requires=['COV-001']),
    CheckDefinition(
        'STR-003', 'Data path traces to the external data pin',
        'The data path must end at (for outputs) or start from (for inputs) the device data pin.',
        did='3.x.3.1 d', requires=['COV-001']),
    CheckDefinition(
        'STR-004', 'Clock paths are the same for setup and hold',
        'The setup and hold analyses must use the same physical clock paths, only with different '
        'delays. Different routes indicate the two checks are timing different clock '
        'relationships.',
        did='3.x.3.1 g', requires=['STR-002']),
    CheckDefinition(
        'STR-005', 'CRPR taken at the common point of the clock paths',
        'Clock pessimism removal must equal the delay difference of the clock path elements the '
        'launch and capture paths share, up to the point where they diverge. A different value '
        'means pessimism is removed from the wrong point.',
        did='3.x.3.1 b', requires=['STR-001']),
    CheckDefinition(
        'EDG-001', 'Setup check uses the intended launch and capture edges',
        'The launch and capture edges of the setup check, and their directions, must match the '
        'numbered launch edge and lettered setup capture edge in the device intent.',
        did='3.x.3.1 f', requires=['COV-001']),
    CheckDefinition(
        'EDG-002', 'Hold check uses the intended launch and capture edges',
        'The launch and capture edges of the hold check, and their directions, must match the '
        'numbered launch edge and lettered hold capture edge in the device intent.',
        did='3.x.3.1 f', requires=['COV-001']),
    CheckDefinition(
        'DLY-001', 'Max input/output delay matches datasheet and board',
        'The max output or input delay used by the setup check must equal the value derived from '
        'the part datasheet parameters and the board trace delays.',
        did='3.x.3.1 e', requires=['COV-001', 'INT-001']),
    CheckDefinition(
        'DLY-002', 'Min input/output delay matches datasheet and board',
        'The min output or input delay used by the hold check must equal the value derived from '
        'the part datasheet parameters and the board trace delays.',
        did='3.x.3.1 e', requires=['COV-001', 'INT-001']),
    CheckDefinition(
        'SLK-001', 'Setup slack is positive',
        'Worst setup slack across all reported corners must be zero or positive. Only judged once '
        'the corners, path structure, edges and max delay are confirmed.',
        did='3.x.4 b', requires=['COV-002'] + STRUCTURE + ['EDG-001', 'DLY-001']),
    CheckDefinition(
        'SLK-002', 'Hold slack is positive',
        'Worst hold slack across all reported corners must be zero or positive. Only judged once '
        'the corners, path structure, edges and min delay are confirmed.',
        did='3.x.4 b', requires=['COV-002'] + STRUCTURE + ['EDG-002', 'DLY-002']),
]

BY_ID = {check.check_id: check for check in CHECKS}


def get(check_id):
    return BY_ID[check_id]


def to_rst():
    '''Documentation page listing every check.'''
    lines = ['Checks', '======', '',
             'Every check has a permanent identifier. Numbers are never reused or renumbered.',
             'A check is skipped until the checks it depends on pass.', '']
    for prefix, name in STAGES:
        lines += [f'{name} ({prefix})', '-' * len(f'{name} ({prefix})'), '']
        for check in CHECKS:
            if check.stage != prefix:
                continue
            heading = f'{check.check_id}: {check.title}'
            lines += [heading, '^' * len(heading), '', check.description, '']
            if check.did:
                lines += [f'* DID paragraph: {check.did}']
            lines += [f'* Depends on: {", ".join(check.requires) if check.requires else "none"}', '']
    return '\n'.join(lines)
