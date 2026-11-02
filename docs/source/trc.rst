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
             SDR-SS-O, SDR-SS-RT-DI, SDR-SS-I, DDR-SS-O, DDR-SS-I, or all (see :doc:`methodology`).
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

This stage checks the traces and the part against the timing reports.
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

=======================  ========  ============  ============  ========
Rule                     SDR-SS-O  SDR-SS-O-FLC  SDR-SS-RT-DI  SDR-SS-I
=======================  ========  ============  ============  ========
s0_timing_report_001     X         X             X             P
s0_timing_report_002     X         X             X             P
s0_trace_001             X         X             X             P
s0_data_path_001         X         X
s0_data_path_002                                 X
s0_clock_path_001        X         X
s0_clock_path_002                                X
s1_clock_001             X         X             X             P
s2_clock_001             X         X             X             P
s2_clock_002             X         X             X             P
s2_data_path_001         X         X             X             P
s2_output_delay_001      X         X
s2_output_delay_002      X         X
s2_input_delay_001                               X             P
s2_input_delay_002                               X             P
s3_output_delay_001      X         X
s3_output_delay_002      X         X
s3_input_delay_001                               X             P
s3_input_delay_002                               X             P
s4_process_corner_001    P         P             P             P
s4_process_corner_002    P         P             P             P
s4_data_path_003                                               P
s4_clock_path_002                                              P
s4_launch_clock_001      X         X             X             P
s4_launch_clock_002      X         X             X             P
s4_capture_clock_001     X         X             X             P
s4_capture_clock_002     X         X             X             P
s4_requirement_001       X         X             X             P
s4_requirement_002       X         X             X             P
s4_part_001              X         X
s4_part_002                                      X
s5_slack_001             X         X             X             P
s5_slack_002             X         X             X             P
=======================  ========  ============  ============  ========

``X`` marks a rule stacv checks, and ``P`` a rule that is planned for the methodology.
SDR-SS-O-FLC runs the SDR-SS-O rules unchanged.
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

.. automodule:: stacv.rules.trace.s0_trace_001

s0_data_path_001: Data path ends at the configured port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.data_path.s0_data_path_001

s0_clock_path_001: Capture clock path ends at the configured clock port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s0_clock_path_001

s0_data_path_002: Data path starts at the configured port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.data_path.s0_data_path_002

s0_clock_path_002: Launch clock path ends at the configured clock port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s0_clock_path_002

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

s2_input_delay_001: Input delays match in every setup timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.input_delay.s2_input_delay_001

s2_input_delay_002: Input delays match in every hold timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.input_delay.s2_input_delay_002

Stage 3: Board and Part
-----------------------

s3_output_delay_001: Maximum output delays match the calculated output delays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.output_delay.s3_output_delay_001

s3_output_delay_002: Minimum output delays match the calculated output delays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.output_delay.s3_output_delay_002

s3_input_delay_001: Maximum input delays match the calculated input delays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.input_delay.s3_input_delay_001

s3_input_delay_002: Minimum input delays match the calculated input delays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.input_delay.s3_input_delay_002

Stage 4: Intent
---------------

s4_process_corner_001: A setup and hold timing report exists at each process corner
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Planned: stacv does not check this rule yet.*

Each data port must have at least one setup and one hold timing report at each process corner listed in the device definition.
A missing timing report means the data port is not timed at that corner.
This rule waits for a second timing tool: the Vivado parser accepts only the Slow and Fast process corners, and stage 0 requires both.

s4_process_corner_002: Every timing report is at a process corner listed in the device definition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Planned: stacv does not check this rule yet.*

A timing report at any other process corner is a failure.
It usually means the timing reports were generated for a different device, or with different settings than intended.
This rule waits for a second timing tool: the Vivado parser accepts only the Slow and Fast process corners, and stage 0 requires both.

s4_data_path_003: Data path starts at an input port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Planned: stacv does not check this rule yet.*

The data path in the timing report must start at an input port.

s4_clock_path_002: Capture clock path starts at the interface clock input port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

*Planned: stacv does not check this rule yet.*

The capture clock path in the timing report must start at a port.

s4_launch_clock_001: Launch clock name matches the configured launch clock
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s4_launch_clock_001

s4_launch_clock_002: Launch clock period matches the configured launch clock period
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s4_launch_clock_002

s4_capture_clock_001: Capture clock name matches the configured capture clock
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s4_capture_clock_001

s4_capture_clock_002: Capture clock period matches the configured capture clock period
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.s4_capture_clock_002

s4_requirement_001: Setup requirement matches the configured setup edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.requirement.s4_requirement_001

s4_requirement_002: Hold requirement matches the configured hold edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.requirement.s4_requirement_002

s4_part_001: Capture clock edge is the edge type the part requires
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.part.s4_part_001

s4_part_002: Launch clock edge is the edge type the part launches on
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.part.s4_part_002

Stage 5: Slack
--------------

s5_slack_001: Setup slack is not negative in every timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.slack.s5_slack_001

s5_slack_002: Hold slack is not negative in every timing report
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.slack.s5_slack_002


Rule ideas
----------

These are earlier rule ideas kept as a guide for additional rules.
Their names and numbers are not final.
Each one gets a full entry above, with a unique number, before it is coded.

Multiple Reports

clock_002
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
