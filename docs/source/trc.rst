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
s4_requirement_001       X         X          X
s4_requirement_002       X         X          X
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

.. automodule:: stacv.rules.trace.s0_trace_001

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

:Stage: 4 - configuration
:Applies to: all
:Reads: ``requirement`` of every setup timing report, ``launch_clock.period``, ``launch_clock.setup_edge``, ``capture_clock.period`` and ``capture_clock.setup_edge`` of the port in the configuration
:Depends on: none

The setup requirement in every setup timing report must match the time between the configured setup edges.
Every setup timing report is checked, at every process corner.
The time of an edge is (period / 2) * n, where n is the edge number for the launch clock, and the position of the edge letter for the capture clock, starting at 0 for A.
The expected setup requirement is the time of the capture setup edge minus the time of the launch setup edge.
Only the difference is compared, because the timing tool can time a later pair of edges with the same relationship.
The duty cycle of both clocks is assumed to be 50%, and phase offsets are not considered.
The requirement matches when it is within 0.0005 ns of the expected requirement, half of the last digit printed in the timing report.
If the requirement differs, the timing report does not time the edges the analysis is about, so its results do not apply to the interface.

**Violation**

The port is configured with ``launch_clock = {name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = 8}`` and ``capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50.000, setup_edge = "D", hold_edge = "B"}``.
Edge 8 is at 40.000 ns and edge D is at 75.000 ns, an expected setup requirement of 35.000 ns, but the timing report gives 10.000 ns:

.. code-block:: text
   :emphasize-lines: 2

     Path Type:              Max at Fast Process Corner
     Requirement:            10.000ns  (dac_sclk rise@50.000ns - clk_100mhz rise@40.000ns)

**Result**

When the rule fails, it lists each timing report whose setup requirement differs, with the file and line of the requirement:

.. code-block:: text

     O_DAC_DATA_timing.rpt:82  setup requirement 10.000ns, configured setup requirement 35.000ns

**Likely causes**

* The setup edges in the configuration are wrong.
* A multicycle path constraint for setup is missing, or has the wrong number of cycles.
* The output delay constraint refers to the wrong edge of the capture clock.

Refer to the vendor's timing constraints documentation for multicycle paths and output delays.

s4_requirement_002: Hold requirement matches the configured hold edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Stage: 4 - configuration
:Applies to: all
:Reads: ``requirement`` of every hold timing report, ``launch_clock.period``, ``launch_clock.hold_edge``, ``capture_clock.period`` and ``capture_clock.hold_edge`` of the port in the configuration
:Depends on: none

The hold requirement in every hold timing report must match the time between the configured hold edges.
Every hold timing report is checked, at every process corner.
The time of an edge is (period / 2) * n, where n is the edge number for the launch clock, and the position of the edge letter for the capture clock, starting at 0 for A.
The expected hold requirement is the time of the capture hold edge minus the time of the launch hold edge.
It is negative when the capture hold edge comes before the launch hold edge, which is common for an interface clocked by a divided down clock.
Only the difference is compared, because the timing tool can time a later pair of edges with the same relationship.
The duty cycle of both clocks is assumed to be 50%, and phase offsets are not considered.
The requirement matches when it is within 0.0005 ns of the expected requirement, half of the last digit printed in the timing report.
If the requirement differs, the timing report does not time the edges the analysis is about, so its results do not apply to the interface.

**Violation**

The port is configured with ``launch_clock = {name = "clk_100mhz", period = 10.000, setup_edge = 8, hold_edge = 8}`` and ``capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 50.000, setup_edge = "D", hold_edge = "B"}``.
Edge 8 is at 40.000 ns and edge B is at 25.000 ns, an expected hold requirement of -15.000 ns, but the timing report gives 0.000 ns:

.. code-block:: text
   :emphasize-lines: 2

     Path Type:              Min at Fast Process Corner
     Requirement:            0.000ns  (dac_sclk rise@0.000ns - clk_100mhz rise@0.000ns)

**Result**

When the rule fails, it lists each timing report whose hold requirement differs, with the file and line of the requirement:

.. code-block:: text

     O_DAC_DATA_timing.rpt:21  hold requirement 0.000ns, configured hold requirement -15.000ns

**Likely causes**

* The hold edges in the configuration are wrong.
* A multicycle path constraint for hold is missing, or has the wrong number of cycles.
  When a multicycle path moves the setup edges, the timing tool moves the hold edges with them unless told otherwise.
* The output delay constraint refers to the wrong edge of the capture clock.

Refer to the vendor's timing constraints documentation for multicycle paths and output delays.

s4_part_001: Capture clock edge is the edge type the part requires
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:Stage: 4 - configuration
:Applies to: SDR-SS-O
:Reads: capture clock edge type in the ``requirement`` of every timing report, ``capture_edge`` of the part pin in the part
:Depends on: none

The part states whether each data pin captures on the rising or falling edge of its clock pin.
The capture clock edge in every timing report must be that edge type.
Every timing report is checked, setup and hold, at every process corner.
If the edge type differs, the timing report times the data against an edge the part does not capture on.

**Violation**

The part pin is configured with ``capture_edge = "Falling"``, but the timing report times the rising edge of ``dac_sclk``:

.. code-block:: text
   :emphasize-lines: 2

     Path Type:              Max at Fast Process Corner
     Requirement:            10.000ns  (dac_sclk rise@50.000ns - clk_100mhz rise@40.000ns)

**Result**

When the rule fails, it lists each timing report whose capture clock edge type differs, with the file and line of the requirement:

.. code-block:: text

     O_DAC_DATA_timing.rpt:82  capture clock edge rise, part SDIN captures on Falling

**Likely causes**

* The output delay constraint refers to the wrong edge of the capture clock.
* The capture edge of the pin in the part file is wrong.
* The configured capture edges are the wrong edge type, and the timing constraints were written to match them.

Refer to the vendor's timing constraints documentation for output delays.

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
