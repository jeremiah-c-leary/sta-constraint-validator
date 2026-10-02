Timing Rule Checks
==================

Each rule is documented here before it is coded.
The documentation states what the rule compares and which timing report values it reads, so the tests can be written against it.

Report excerpts in the examples are from Vivado.
The rules themselves apply to timing reports from any vendor.

Rules
-----

clock_001: Launch and capture clock paths start at the same point
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. automodule:: stacv.rules.clock.clock_001

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

