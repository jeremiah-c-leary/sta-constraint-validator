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

:Compares: within one timing report
:Reads: ``launch_clock_path`` first delay, ``capture_clock_path`` first delay
:Depends on: none

The launch clock path and the capture clock path must start at the same clock source.
In a forwarded clock interface, both clocks come from one input clock.
If the paths start at different points, the relationship between the clocks is not defined by the design, and clock pessimism removal has no common section to work from.

**Violation**

The launch clock path starts at ``I_CLK`` and the capture clock path starts at ``I_CLK2``:

.. code-block:: text
   :emphasize-lines: 4, 11

       ---------------------------------------------------------------------------------------
                            (clock clk_100mhz rise edge)     0.000     0.000 r
       K18                                               0.000     0.000 r  I_CLK (IN)
                            net (fo=0)                   0.000     0.000    I_CLK
       K18                  IBUF (Prop_ibuf_I_O)         0.160     0.160 r  I_CLK_IBUF_inst/O
       ---------------------------------------------------------------------------------------
                                   ...
       ---------------------------------------------------------------------------------------
                            (clock dac_sclk rise edge)     0.000     0.000 r
       L17                                               0.000     0.000 r  I_CLK2 (IN)
                            net (fo=0)                   0.000     0.000    I_CLK2
       L17                  IBUF (Prop_ibuf_I_O)         0.348     0.348 r  I_CLK2_IBUF_inst/O

**Likely causes**

* The generated capture clock was created from the wrong master clock.
* The two input clocks reach the logic through a clock mux.
  The timing tool times each side through whichever branch is worst for the check.
  For setup, that is the longer branch on launch and the shorter branch on capture.

Refer to the vendor's timing constraints documentation for generated clocks and clock muxes.

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

