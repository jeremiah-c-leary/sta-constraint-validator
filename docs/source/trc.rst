Timing Rule Checks
==================

Timing Rule Checks ensure the provided timing reports are valid and meet what the user intends to time.
Each rule has a unique identifier and is individually documented.
The documentation includes examples to help the user identify where the issues are located.
The examples include timing reports from Vivado, but the rules apply to any supported vendor.

Rule names
----------

A rule is named after its stage, its subject and a number, for example ``s1_clock_001``.

Each rule lists these fields:

:Stage: When the rule runs (see `Stages`_).
:Applies to: The methodology the rule checks:
             SDR-SS-O, SDR-SS-RT, SDR-SS-I, DDR-SS-O, DDR-SS-I, or all (see :doc:`methodology`).
:Reads: The timing report values the rule uses.
:Depends on: Rules that must pass before this rule is checked.

Stages
------

The Timing Rule Checks are run in six stages:

#. Stage 0: Input Checks
#. Stage 1: Intra-Timing Report
#. Stage 2: Inter-Timing Report
#. Stage 3: Board and Part
#. Stage 4: Intent
#. Stage 5: Slack

Each stage depends on the checks in the stages before it.
If an issue is found during a stage, then future stages will not be executed.

Input Checks
^^^^^^^^^^^^

This stage checks input files for issues.

Intra-Timing Report
^^^^^^^^^^^^^^^^^^^

This stage checks for issues within a single timing report.
This stage provides rules that apply to every timing report regardless of intent.

Inter-Timing Report
^^^^^^^^^^^^^^^^^^^

This stage checks for consistency across multiple related timing reports.
This stage provides rules to ensure the setup and hold timing reports across all corners are valid.

Board and Part
^^^^^^^^^^^^^^

This stage checks the board data and the part against the timing reports.
It checks that the output and input delays in the timing reports match the delays calculated from the trace delays and the part.

Intent
^^^^^^

This stage checks the user's intended timing against the timing reports.
The intent comes from the methodology and the device definition: the ports, clocks, edges and process corners.

Slack
^^^^^

This stage checks the slack of every timing report.
It runs last, so the slack is known to come from the intended timing.

Methodology coverage
^^^^^^^^^^^^^^^^^^^^

=======================  ========  =========  ========
Rule                     SDR-SS-O  SDR-SS-RT  SDR-SS-I
=======================  ========  =========  ========
s3_trace_001             X         X          X
s3_part_001              X         X          X
s3_part_002              X         X          X
s3_output_delay_001      X
s3_input_delay_001                 X          X
s4_process_corner_001    X         X          X
s4_process_corner_002    X         X          X
s4_timing_report_001     X         X          X
s4_data_path_001         X
s4_data_path_002                   X
s4_data_path_003                              X
s4_clock_path_001        X
s4_clock_path_002                             X
s4_launch_clock_001      X         X          X
s4_launch_clock_002      X         X          X
s4_capture_clock_001     X         X          X
s4_capture_clock_002     X         X          X
s4_launch_edge_001       X         X          X
s4_capture_edge_001      X         X          X
s5_slack_001             X         X          X
s5_slack_002             X         X          X
=======================  ========  =========  ========

The columns are the methodologies described in :doc:`methodology`.
The DDR methodologies are added once their rules are defined.

Stage 0: Input Checks
---------------------

s0_timing_report_001: Setup timing reports must exist for at least two process corners
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.timing_report.s0_timing_report_001

s0_timing_report_002: Hold timing reports must exist for at least two process corners
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.timing_report.s0_timing_report_002

s0_trace_001: A data trace and its clock trace connect the port to the part
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The data trace is the trace whose device pin is the port name and whose part pin is a pin of the part.
The clock trace is the trace whose device pin is the port's capture clock port and whose part pin is the clock pin of that part pin.
Both traces must give device to part delays.
Without both traces, the output delays cannot be calculated.

s0_trace_002: Every pin of the device interface has a trace in the board data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The traces connect the part pins to the device ports.
A pin without a trace has no device port, so it cannot be timed and its output or input delay cannot be calculated.
The device pin of the trace must be the port name as it appears in the timing reports.

s0_part_001: Every part data pin is referenced to a clock pin of its interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The setup and hold, or clock to out, of a part data pin are given relative to one part clock pin.
That clock pin must belong to the same interface, so its trace gives the clock port.

Stage 1: Intra-Timing Report
----------------------------

s1_clock_001: Launch and capture clock paths start at the same point
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s1_clock_001

Stage 2: Inter-Timing Report
----------------------------

s2_clock_001: Launch clock paths pass through the same elements in every timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s2_clock_001

s2_clock_002: Capture clock paths pass through the same elements in every timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s2_clock_002

s2_data_path_001: Data paths pass through the same elements in every timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.data_path.s2_data_path_001

s2_output_delay_001: Output delays match in every setup timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.output_delay.s2_output_delay_001

s2_output_delay_002: Output delays match in every hold timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.output_delay.s2_output_delay_002

Stage 3: Board and Part
-----------------------

s3_output_delay_001: Maximum output delays match the calculated output delays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.output_delay.s3_output_delay_001

s3_output_delay_002: Minimum output delays match the calculated output delays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.output_delay.s3_output_delay_002

Stage 4: Intent
---------------

s4_process_corner_001: A setup and hold timing report exists at each process corner
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Each data port must have at least one setup and one hold timing report at each process corner listed in the device definition.
A missing timing report means the data port is not timed at that corner.

s4_process_corner_002: Every timing report is at a process corner listed in the device definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A timing report at any other process corner is a failure.
It usually means the timing reports were generated for a different device, or with different settings than intended.

s4_timing_report_001: Every timing report matches a data port of a methodology
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A timing report that matches no data port is not checked by any other rule, so it is a failure.
It usually means a data port is missing from the methodology, or the wrong timing report was provided.

s4_data_path_001: Data path ends at an output port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The data path in the timing report must end at an output port.

s4_data_path_002: Data path includes clock output pin and data input pin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The data path must include the clock output port and a data input port.

s4_data_path_003: Data path starts at an input port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The data path in the timing report must start at an input port.

s4_clock_path_001: Clock path ends at an output port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The capture clock path in the timing report must end at a port.

s4_clock_path_002: Capture clock path starts at the interface clock input port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The capture clock path in the timing report must start at a port.

s4_launch_clock_001: Launch clock name intent matches timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The clock that launches the data in every timing report must be the intended launch clock.

s4_launch_clock_002: Launch clock frequency intent matches timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The period of the launch clock in every timing report must match the intended frequency.
The comparison allows for the rounding of the period in the timing report.

s4_capture_clock_001: Capture clock name intent matches timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The clock that captures the data in every timing report must be the intended capture clock.

s4_capture_clock_002: Capture clock frequency intent matches timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The period of the capture clock in every timing report must match the intended frequency.
The comparison allows for the rounding of the period in the timing report.

s4_launch_edge_001: Launching clock edge intent matches timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The rising or falling edge of the launch clock matches between intent and timing reports.

s4_capture_edge_001: Capture clock edge intent matches timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The rising or falling edge of the capture clock matches between intent and timing reports.

s4_part_001: Edges at the part clock are the edge type the part requires
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The part states whether each data pin is timed on the rising or falling edge of its clock pin.
The edges given in the device for the clock at the part must be of that type.
For SDR-SS-O, these are the capture edges: a part that captures on the falling edge needs B, D, F, ...

Stage 5: Slack
--------------

s5_slack_001: Setup slack is not negative in every timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Setup slack must be zero or positive at every process corner.

s5_slack_002: Hold slack is not negative in every timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Hold slack must be zero or positive at every process corner.


Rule ideas
----------

These are earlier rule ideas kept as a guide for additional rules.
Their names and numbers are not final.
Each one gets a full entry above, with a unique number, before it is coded.

Multiple Reports

clock_004
^^^^^^^^^

This rule checks the starting clock point of the  is the same between all timing reports.

clock_003
^^^^^^^^^

This rule checks the data clock path is the same between all timing reports.

clock_004
^^^^^^^^^

This rule checks the required clock path is the same between all timing reports.

clock_005
^^^^^^^^^

This rule checks for deviations in clock paths

output_delay_001
^^^^^^^^^^^^^^^^

This rule checks the output_delay value is correct.


operating_conditions_001
^^^^^^^^^^^^^^^^^^^^^^^^

This rule checks for setup and hold reports exist for at least two corners
