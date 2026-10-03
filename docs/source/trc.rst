Timing Rule Checks
==================

Each rule is documented here before it is coded.
The documentation states what the rule checks and which timing report values it reads, so the tests can be written against it.

Report excerpts in the examples are from Vivado.
The rules themselves apply to timing reports from any vendor.

Rule names
----------

A rule is named after its subject and a number, for example ``clock_001``.
The name is permanent.
It does not change when a rule moves to another stage, and a number is never reused.

Each rule lists these fields:

:Stage: When the rule runs (see `Stages`_).
:Applies to: The type of timing path the rule checks:
             output interface (write to the part), input interface, round trip (read from the part), or all.
:Reads: The timing report values the rule uses.
:Depends on: Rules that must pass before this rule is checked.

Stages
------

The rules run in stages.
A stage is only checked when the stage before it passes.

1. Within one timing report: each report is checked on its own.
2. Across timing reports: reports for the same interface are compared with each other.
3. Timing report against intent: reports are compared with the device, part and board intent.

Stage 1: Within one timing report
---------------------------------

clock_001: Launch and capture clock paths start at the same point
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.clock_001

data_path_001: Data path ends at an output port
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.data_path.data_path_001

Stage 2: Across timing reports
------------------------------

No rules yet.

Stage 3: Timing report against intent
-------------------------------------

No rules yet.

Rule ideas
----------

These are earlier rule ideas kept as a guide for additional rules.
Their names and numbers are not final.
Each one gets a full entry above, with a unique number, before it is coded.

clock_002
^^^^^^^^^

This rule checks the launch edge is correct for each timing report.


clock_003
^^^^^^^^^

This rule checks the capture edge is correct for each timing report.


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

