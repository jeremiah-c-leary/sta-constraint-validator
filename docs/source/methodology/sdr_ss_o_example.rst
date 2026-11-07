.. How stacv and Vivado do each step of SDR-SS-O on the DAC81404's O_DAC_DATA.  The concept page (sdr_ss_o.rst)
   explains why; this page changes when a command or a key changes.

SDR-SS-O Worked Example: the DAC81404's O_DAC_DATA
==================================================

This page does each step of :doc:`sdr_ss_o` with stacv and Vivado, on the DAC81404 example in ``example/texas_instruments/DAC81404``.
Each step shows the lines of the files it uses, the command, and what the command writes.
The commands are run in the example's directory.

The interface
-------------

The device's port O_DAC_DATA drives the DAC81404's data input SDIN, which the DAC captures on the falling edge of its clock, SCLK.
The device forwards that clock on its port O_DAC_SCLK.

Three files describe the interface, each written by the person who knows it:

==================  ===================================================  ==============================
File                Describes                                            Written from
==================  ===================================================  ==============================
``part.toml``       The DAC81404's pins and their timing                 the DAC81404's datasheet
``traces.toml``     The traces between the device and the DAC81404       the HW engineer's board values
``interface.toml``  The device's clocks and ports                        the designer's clock plan
==================  ===================================================  ==============================

``stacv visualize block_diagram interface.toml`` draws how they connect:

.. code-block:: text

   ----------------+                       +------------
     Device        |                       |  DAC81404
                   |                       |
     O_DAC_DATA   [X] --- data_output --> [X] SDIN
                   |                       |
     O_DAC_SDEN_F [X] --- chip_select --> [X] CSF
                   |                       |
     I_DAC_DATA   [X] <-- data_input ---- [X] SDO
                   |                       |
     O_DAC_SCLK   [X] --- clock --------> [X] SCLK
                   |                       |
   ----------------+                       +------------

This page times the first row, O_DAC_DATA to SDIN, and its clock, O_DAC_SCLK to SCLK.

Where the information goes
--------------------------

Each piece of information the concept page lists goes in one key of one file.
The keys are named as stacv's error messages name them, so a message about a key points to the same place.

=====  =================================================  ==================  ==================================================================  ===============================
ID     Information                                        File                Key                                                                 Value
=====  =================================================  ==================  ==================================================================  ===============================
I1     The launch clock and its period                    ``interface.toml``  key "period" of clock clk_100mhz                                    10 ns
I2     The register that launches the data                ``interface.toml``  key "registers" in port O_DAC_DATA                                  q_spi_output_data_reg
I3     The register that launches the forwarded clock     ``interface.toml``  key "source" in generator of clock dac_sclk                          q_spi_output_clock_reg
I4     The forwarded clock's period, and its port         ``interface.toml``  keys "period" and "port" of clock dac_sclk                          40 ns, O_DAC_SCLK
I5     The edge the part captures on                      ``part.toml``       key "capture_edge" in pin SDIN of interface Serial Interface        Falling
I6     The part's setup and hold                          ``part.toml``       keys "setup" and "hold" in pin SDIN of interface Serial Interface   10 ns, 10 ns
I7     The data trace's delays                            ``traces.toml``     key "device_to_part" in trace data_output                           3 ns, 1 ns
I8     The clock trace's delays                           ``traces.toml``     key "device_to_part" in trace clock                                 3 ns, 1 ns
I9     The launch and capture edges                       ``interface.toml``  keys "launch_clock" and "capture_clock" in port O_DAC_DATA          setup 8 to D, hold 8 to B
=====  =================================================  ==================  ==================================================================  ===============================

The divide of the forwarded clock is not written: stacv works it out from the two periods.

The traces name the signal they carry, such as COPI, instead of their pins; stacv links each to the port and the part pin that carry the same signal (see :doc:`../standards`).
That is how the trace data_output reaches O_DAC_DATA and SDIN.

Steps
-----

1. Choose the launch and capture edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 1 of :doc:`sdr_ss_o`.
The clocks, and the edges of O_DAC_DATA (I1, I4, I9), are in ``interface.toml``:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/interface.toml
   :language: toml
   :start-at: [[clock]]
   :end-before: [[port]]
   :lineno-match:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/interface.toml
   :language: toml
   :start-at: [[port]]
   :end-before: [[port]]
   :lineno-match:

dac_sclk_rd is the slower clock the DAC81404 is read with; O_DAC_DATA does not use it.

The edge the part captures on (I5) is in ``part.toml``, with the part's setup and hold (step 3):

.. literalinclude:: ../../../example/texas_instruments/DAC81404/part.toml
   :language: toml
   :start-at: [[interface.pin]]
   :end-before: [[interface.pin]]
   :lineno-match:

``stacv visualize edges interface.toml`` draws the edges of each port:

.. code-block:: text

                                                                                1     1     1     1     1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                                                    |---setup requirement-->|
                                            |<---hold requirement---|

                    A_______________________B                       C_______________________D                       E
   dac_sclk       __|                       |_______________________|                       |_______________________|
   (25 MHz)


   setup requirement = 20 ns
   hold requirement = -20 ns

Compare the drawing with the part's datasheet: the data changes with the rising edge C, and the DAC81404 captures it on the falling edges B and D.
Adjust the setup and hold edges as necessary to and use ``stacv visualize edges interface.toml`` to visualize them to ensure the correct edges are being used.
An edge that does not suit the methodology is reported under the drawing, and every other command stops on it.

2. Create the forwarded clock
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 2 of :doc:`sdr_ss_o`.
The element that generates dac_sclk (I3) is its generator, in the clock's table above: q_spi_output_clock_reg, from clk_100mhz at its pin C to its pin Q.

``stacv generate xdc interface.toml --output if_dac81404.xdc`` writes the constraints.
Section 4.1 creates dac_sclk at the element:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/if_dac81404.xdc
   :language: text
   :start-at: # -name:       the name of the generated clock
   :end-at: create_generated_clock -name dac_sclk
   :lineno-match:

3. Calculate the output delays
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 3 of :doc:`sdr_ss_o`.
The part's setup and hold (I6) are SDIN's ``setup`` and ``hold`` above.
The data trace (I7) and the clock trace (I8) are in ``traces.toml``:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/traces.toml
   :language: toml
   :start-at: [[trace]]
   :end-before: [[trace]]
   :lineno-match:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/traces.toml
   :language: toml
   :start-at: name = "clock"
   :end-before: # This is for
   :lineno-match:

Section 5.1 of the constraints writes the output delays, with their calculation:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/if_dac81404.xdc
   :language: text
   :start-at: # -clock:                the capture clock
   :end-at: -min -12.000 [get_ports O_DAC_DATA]
   :lineno-match:

``-reference_pin`` is how Vivado times the output delay against the clock at the clock port, as the concept page describes: it adds the clock's path from q_spi_output_clock_reg to O_DAC_SCLK to the timing.

4. Set the multicycle paths
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Step 4 of :doc:`sdr_ss_o`.
There is nothing more to write: the multicycle paths follow from the edges of step 1, and section 5.1 writes them with their calculation:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/if_dac81404.xdc
   :language: text
   :start-at: # multiplier:  setup requirement / launch period
   :end-at: set_multicycle_path 3 -hold -start -from [get_clocks clk_100mhz] -to [get_ports O_DAC_DATA]
   :lineno-match:

5. Run the timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^

Each timing report of O_DAC_DATA must time the path through the port to the forwarded clock, at each process corner, from each register that drives the port.
The registers (I2) and the timing report files are in the port's table:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/interface.toml
   :language: toml
   :start-at: registers = ["q_spi_output_data_reg"]
   :end-before: [[port]]
   :lineno-match:

``stacv generate report_tcl interface.toml --output if_dac81404_stacv_report.tcl`` writes the Vivado script that writes them.
Source it in Vivado after implementation, with the constraints applied.
For each corner, it writes the setup and hold reports of O_DAC_DATA to its file:

.. literalinclude:: ../../../example/texas_instruments/DAC81404/if_dac81404_stacv_report.tcl
   :language: tcl
   :start-at: config_timing_corners -corner Slow -delay_type min_max
   :end-before: # O_DAC_SDEN_F
   :lineno-match:

6. Check the timing reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^

``stacv check interface.toml`` checks each port's timing reports in stages, each stage building on the one before (see :doc:`../trc`):

.. code-block:: text

   Reading interface file interface.toml
   Reading timing report file timing_reports/O_DAC_DATA_timing.rpt
   PASSED: O_DAC_DATA.SDR-SS-O
   Reading timing report file timing_reports/O_DAC_SDEN_F_timing.rpt
   PASSED: O_DAC_SDEN_F.SDR-SS-O-FLC
   Reading timing report file timing_reports/I_DAC_DATA_timing.rpt
   PASSED: I_DAC_DATA.SDR-SS-RT-DI
   Check Passed

Debugging a failing check
"""""""""""""""""""""""""

Here the constraints were applied without ``-reference_pin``.
Vivado reports no problem, and the setup and hold slacks look healthy, but ``stacv check`` fails:

.. code-block:: text

   Reading interface file interface.toml
   Reading timing report file timing_reports/O_DAC_DATA_timing.rpt
   FAILED: [s0_clock_path_001] O_DAC_DATA.SDR-SS-O
       timing_reports/O_DAC_DATA_timing.rpt:61  capture clock path ends at q_spi_output_clock_reg/Q, configured clock port O_DAC_SCLK
       timing_reports/O_DAC_DATA_timing.rpt:118  capture clock path ends at q_spi_output_clock_reg/Q, configured clock port O_DAC_SCLK
       ...

#. **The rule.**  The failure names the rule, s0_clock_path_001.
   Its entry in :doc:`../trc` says what it checks: the capture clock path of every timing report ends at the clock port, so the report times the data against the clock as the part sees it.
#. **The timing report.**  Each line of the failure points to a line of a timing report, here line 61, the last line of the capture clock path:

   .. code-block:: text

          SLICE_X0Y7           FDCE (Prop_fdce_C_Q)         0.279    24.009 f  q_spi_output_clock_reg/Q
                               clock pessimism              0.222    27.875

   The path stops at the register's output: the clock's path through the output buffer to O_DAC_SCLK is missing.
#. **The constraint.**  The capture clock path ends where the output delay's clock is measured.
   In section 5.1 of the constraints, set_output_delay names the clock, dac_sclk, and ``-reference_pin [get_ports O_DAC_SCLK]`` measures it at the port; without it, Vivado measures it where the clock is created, at q_spi_output_clock_reg/Q.
#. **The fix.**  Apply the constraints stacv generates, with ``-reference_pin``, run the report script again, and run ``stacv check`` again.

Pitfalls
--------

Mistakes Vivado does not report, with the step that avoids each and the rule that catches it.
Each was confirmed by checking a timing report with the mistake in it:

======================================================================  ======  =====================
Mistake                                                                 Step    Caught by
======================================================================  ======  =====================
No ``-reference_pin`` on the output delays                              3       s0_clock_path_001
Output delays typed by hand that do not match the part or the traces    3       s3_output_delay_001,
                                                                                s3_output_delay_002
Timing met on Vivado's default edges                                    4       s4_requirement_001,
                                                                                s4_requirement_002
A report that times another register                                    5       s0_register_001
A report that times another clock                                       5       s4_capture_clock_001,
                                                                                s4_capture_clock_002
======================================================================  ======  =====================

