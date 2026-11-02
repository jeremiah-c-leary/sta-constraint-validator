Methodologies
=============

A methodology defines how to perform a timing analysis a single signal between devices.
These methodologies are defined relative to the device being timed.

The following represent a subset of named methodologies:

============= ==================================================================
Identifier    Name
============= ==================================================================
SDR-SS-O      Single Data Rate (SDR) Source Synchronous (SS) Output (SDR-SS-O)
SDR-SS-O-FLC  SDR SS Output to the First and Last Clock (SDR-SS-O-FLC)
SDR-SS-RT-DI     SDR SS Round Trip (SDR-SS-RT-DI)
SDR-SS-I      SDR SS Input (SDR-SS-I)
DDR-SS-O      Double Data Rate (DDR) SS Output (DDR-SS-O)
DDR-SS-I      DDR SS Input (DDR-SS-I)
============= ==================================================================

An interface, such as SPI, could use more than one methodology.
For example, an SPI interface to a DAC could use:

========= ==============
Pin       Methodology
========= ==============
MOSI      SDR-SS-O
CS_F      SDR-SS-O-FLC
MISO      SDR-SS-RT-DI
========= ==============

An interface is considered fully timed when the methodology of each pin is validated.

The part defines the methodology of each of its pins.
The pins are grouped into interfaces, and a part can have more than one interface.
The methodology names of the part pins are from the part's point of view:
a part input pin, which the device drives, is ``SDR-SS-I`` (see :doc:`part`).

Each interface is timed independently, with its own interface, traces and part files.
The traces connect each pin of the part interface to a device port.
If a device connects to two of the same part, each connection is a separate interface with its own files.

Not supported yet
-----------------

* Methodologies other than SDR-SS-O, SDR-SS-O-FLC and SDR-SS-RT-DI: a port with another methodology can be listed with ``status = "defer"`` until it is supported (see :doc:`interface`).
* Buses: give each bit its own ``[[port]]`` (interface_config_022).
* A device port shared by two interfaces, such as a shared SPI bus.
  Each interface would calculate its own output delay for the shared port, but the timing reports carry only one.
* Pins without a clock, such as the DAC81404 LDAC pin: it has no setup and hold to a clock edge, so no methodology times it.

.. The terms are layered:
.. 
.. ==============  =====================================================================
.. Term            Meaning
.. ==============  =====================================================================
.. Interface       A set of signals between the device and a part, for example SPI.
.. Methodology     How one or more signals of the interface are timed.
.. Timing report   One setup or hold check reported by the timing tool.
.. Timing path     The launch clock, data or capture clock path within a timing report.
.. ==============  =====================================================================

.. 
.. Each methodology documents:
.. 
.. * the information the user provides
.. * how timing reports are matched to it
.. * which timing reports must exist
.. * which rules are checked
.. * what stacv reports

Single Data Rate Source Synchronous Output (SDR-SS-O)
-----------------------------------------------------

The device launches data on an internal clock and forwards a clock on an output port.
The part captures the data with the forwarded clock.
The launch clock could be an integer multiple of the capture clock.

.. code-block:: text

     Device                                                  Part
   +--------------------------------------+          +-----------+
   |                                      |          |           |
   |  launch clock --+--> [FF] --data--> [X] -----> [X] data in  |
   |                 |                    |          |           |
   |                 +--> [FF] --clock-> [X] -----> [X] clock in |
   |                                      |          |           |
   +--------------------------------------+          +-----------+

The timing tool checks the data at the data port against the forwarded clock at the clock port.
The part's setup and hold requirements, and the trace delays, are given to the timing tool as output delays.
stacv calculates the output delays itself and checks that the timing reports use them.

Information sources
^^^^^^^^^^^^^^^^^^^

Each file provides only the information its author knows:

==============  =================================================================  ==================================
Source          Provides                                                           Example
==============  =================================================================  ==================================
Part            The pins of each part interface and the methodology of each pin.   ``SDIN``: SDR-SS-I
Part            The clock pin each data pin is referenced to.                      ``SCLK``
Part            The setup and hold of each data pin, and the clock edge they       10 ns, 10 ns on the falling edge
                apply to (:doc:`part`).
Traces          The trace from each part pin to a device port, and its delays      ``SDIN`` to ``O_DAC_DATA``
                (:doc:`traces`).
Interface       The clocks, their periods, and the port the capture clock          ``clk_100mhz``, 10 ns;
                leaves the device on.                                              ``dac_sclk``, 40 ns, ``O_DAC_SCLK``
Interface       Each port, its methodology, and its setup and hold launch and      8, D and 8, B
                capture edges (:doc:`interface`).
Timing reports  What the timing tool timed, and the process corners it timed at.   Slow, Fast
==============  =================================================================  ==================================

The user does not provide the output delays.
They are calculated from the part and the traces (see `Output delay calculation`_), written into the constraints by ``stacv generate xdc``, and checked in the timing reports by ``stacv check``.

Clock edges
"""""""""""

The launch and capture edges are the most important information the user provides.
A timing report only proves timing is met if it times the intended edges.
A timing report that meets timing on the wrong edges is not valid.

The user states which edges are intended, not the time of each edge.
stacv checks that the requirement in each timing report is the time between the intended edges.

Each clock is expanded from 0 ns, with a rising edge as the first edge.
The first rising edge is edge 0 or A, whatever its time.
A phase offset changes the time of the edges, not their labels.
For example, a clock with a rising edge at 1.25 ns starts with edge 0 or A at 1.25 ns.

Every edge is counted, rising and falling in turn:

* Launch clock edges are numbered: 0, 1, 2, 3, ...
* Capture clock edges are lettered: A, B, C, D, ...
  After Z, the letters continue AA, AB, ... AZ, BA, BB, ...

Even numbers and the letters A, C, E, ... are rising edges.
Odd numbers and the letters B, D, F, ... are falling edges.
The edges are expanded as far as needed to cover any multicycle path.

The part states whether each data pin is timed on the rising or falling edge of its clock pin.
stacv checks that the timing reports time an edge of that type (``s4_part_001``).

An SDR-SS-O port launches each bit once, so its setup and hold launch edges are the same edge.
Its hold capture edge is the capture edge of the same type before its setup capture edge.
Other edges are an error in the interface file (see :doc:`interface`).

This is the DAC81404 data port, drawn by ``stacv visualize edges``:

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

The setup check launches on edge 8 and captures on the falling edge D.
The hold check launches on the same edge 8 and captures on the falling edge before D, B.

Output delay calculation
""""""""""""""""""""""""

An output delay in the timing constraints must account for the part's setup and hold requirements and the trace delays.
If the user provided the output delays, stacv would only check that the same number was typed twice.
Instead, stacv calculates the output delays from the part and the traces.

Each trace connects a part pin to a device port.
The ``device_pin`` of a trace is the port name as it appears in the timing reports.
For each SDR-SS-O port, stacv finds:

* the data trace: the trace whose device pin is the port; its part pin is the data pin
* the clock trace: the trace from the capture clock's ``port`` to the clock pin of the data pin
* the setup and hold of the data pin, from the part

.. code-block:: text

   Device                Board                  Part
   O_DAC_DATA  ------- data trace -------->  SDIN   setup and hold relative to SCLK
   O_DAC_SCLK  ------- clock trace ------->  SCLK

The output delays are:

.. code-block:: text

   setup (max) output delay = setup of the data pin + data trace max delay - clock trace min delay
   hold (min) output delay  = data trace min delay - clock trace max delay - hold of the data pin

For the DAC81404, with a setup and hold of 10 ns and both traces 1 to 3 ns:

.. code-block:: text

   setup (max) output delay = 10 + 3 - 1 =  12 ns
   hold (min) output delay  =  1 - 3 - 10 = -12 ns

If a trace is missing, ``stacv generate xdc`` stops with an error (generate_007 to generate_009, see :doc:`errors`), and ``stacv check`` fails ``s0_trace_001``.

Timing reports
^^^^^^^^^^^^^^

The timing reports of a port are listed in its ``timing_reports`` key (see :doc:`interface`), and ``stacv generate report_tcl`` writes the Vivado script that creates them.
Every timing report listed is checked against the port.

The process corners are read from the timing reports: each timing report states the process corner it was timed at.
Each port must have at least one setup and one hold timing report at each process corner:

=======  ====  ====
Corner   Max   Min
=======  ====  ====
Slow     X     X
Fast     X     X
=======  ====  ====

Max timing reports are setup checks and min timing reports are hold checks.
A port can have more than one timing report per corner, for example one for each source register.

Rules
^^^^^

These rules are checked on the timing reports of each port.
The stages run in order, as described in :doc:`trc`, and a stage is skipped when an earlier stage fails.

=======  =====================  ==================================================================
Stage    Rule                   Checks
=======  =====================  ==================================================================
0        s0_timing_report_001   A setup timing report exists at each process corner.
0        s0_timing_report_002   A hold timing report exists at each process corner.
0        s0_trace_001           A data trace and its clock trace connect the port to the part.
0        s0_data_path_001       The data path ends at the port.
0        s0_clock_path_001      The capture clock path ends at the capture clock's port.
1        s1_clock_001           The launch and capture clock paths start at the same point.
2        s2_clock_001           The launch clock path is the same in every timing report.
2        s2_clock_002           The capture clock path is the same in every timing report.
2        s2_data_path_001       The data path is the same in every timing report.
2        s2_output_delay_001    The output delay is the same in every setup timing report.
2        s2_output_delay_002    The output delay is the same in every hold timing report.
3        s3_output_delay_001    The maximum output delay matches the calculated output delay.
3        s3_output_delay_002    The minimum output delay matches the calculated output delay.
4        s4_capture_clock_001   The capture clock name matches the interface.
4        s4_capture_clock_002   The capture clock period matches the interface.
4        s4_launch_clock_001    The launch clock name matches the interface.
4        s4_launch_clock_002    The launch clock period matches the interface.
4        s4_part_001            The capture clock edge is the edge type the part requires.
4        s4_requirement_001     The setup requirement is the time between the setup edges.
4        s4_requirement_002     The hold requirement is the time between the hold edges.
5        s5_slack_001           Setup slack is not negative.
5        s5_slack_002           Hold slack is not negative.
=======  =====================  ==================================================================

Results
^^^^^^^

``stacv check`` prints a result for each port (see :doc:`process`).
With ``--report``, it also writes a report file with a summary, the md5sum of every input, and each rule's result and details.
With ``--junit``, it writes a JUnit file with one testsuite for each port, named ``<port>.<methodology>``, and one testcase for each rule.
A failing rule is a failure in its testcase and names the timing report file and line.

Example input
^^^^^^^^^^^^^

The DAC81404 example in ``example/texas_instruments/DAC81404`` times this methodology on ``O_DAC_DATA``.
Its interface file:

.. literalinclude:: ../../example/texas_instruments/DAC81404/interface.toml
   :language: toml

Its part and traces files are ``part.toml`` and ``traces.toml`` in the same directory, described in :doc:`part` and :doc:`traces`.

Single Data Rate Source Synchronous Output to the First and Last Clock (SDR-SS-O-FLC)
--------------------------------------------------------------------------------------

Some signals are timed to the first and last edges of a clock that stops between transfers, rather than to every edge.
A chip select is the usual example: its setup is to the first clock edge after it is asserted, and its hold is from the last clock edge before it is released.
The clock is idle before the first edge and after the last.

The timing tool assumes every clock runs all the time, so it times the signal as SDR-SS-O, against the edges either side of each change.
SDR-SS-O-FLC therefore uses the SDR-SS-O constraints and checks unchanged.
The part pin is still ``SDR-SS-I``, with the datasheet's setup and hold to the first and last clock edges, such as tCSS and tCSH.

Independent setup and hold edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The key difference from SDR-SS-O is which edges make sense.
A data bit changes once: its setup and hold both come from the same launch edge, so moving the launch edge moves both requirements.
A chip select changes twice, when it is asserted and when it is released.
Its setup comes from the launch edge that asserts it, and its hold from the launch edge that releases it, so each can be moved without changing the other.

The DAC81404 chip select first used the data port's edges, and failed setup by about 10 ns, because tCSS is 30 ns:

.. code-block:: toml

   launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}
   capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}

Moving only the setup launch edge two launch periods earlier gave a 40 ns setup requirement and left the hold requirement at -20 ns, and both met timing:

.. code-block:: toml

   launch_clock = {name = "clk_100mhz", setup_edge = 4, hold_edge = 8}
   capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}

For an SDR-SS-O data port, the same change would also have moved the hold requirement to 0 ns and failed hold.
stacv reports different launch setup and hold edges on an SDR-SS-O port as an error (interface_config_019).

Edges diagram
^^^^^^^^^^^^^

What also differs is the edges diagram, in ``stacv visualize edges`` and in the constraints file.
It is drawn in two windows, so it can be compared with the datasheet figure:

* The setup window, with the clock idle up to its first pulse, and the first clock edge marked.
* The hold window, with the clock idle after its last pulse, and the last clock edge marked.

Each window shows whole clock pulses, so the capture clock of an SDR-SS-O-FLC port needs its ``idle`` level (see :doc:`interface`).
A clock that idles low pulses high, rising then falling; a clock that idles high pulses low.
The DAC81404 chip select, with the passing edges above, captured on the falling edge with the clock idle low:

.. code-block:: text

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                            |---------------setup requirement-------------->|
                                              first clock edge ---->|

                                                                    C_______________________D
   dac_sclk       __________________________________________________|                       |
   (25 MHz)

   setup requirement = 40 ns

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                            |<---hold requirement---|
                       last clock edge ---->|

                    A_______________________B
   dac_sclk       __|                       |________________________________________________
   (25 MHz)

   hold requirement = -20 ns

A label is drawn on the right of its edge, pointing back at it, when there is no room on the left.
Both windows end where the first pulse ends, or at the latest edge of the port when it is later.

A data port on the same clock stays SDR-SS-O: its bits are captured within the transfer, where the clock runs.

Single Data Rate Source Synchronous Round Trip, Data In (SDR-SS-RT-DI)
----------------------------------------------------------------------

A round trip reads data from the part on a clock the device forwards to it.
The device forwards the clock, the part launches the data on it, and the device captures the data with its own clock.
On the DAC81404, ``SDO`` is launched on the rising edge of ``SCLK`` and captured in the device by ``clk_100mhz``.

The launch clock is the forwarded clock, so the launch clock has the ``port`` and the ``generator``, and the capture clock stays inside the device.
The part pin is ``SDR-SS-RT-DO``, with the datasheet's clock to out, such as tSDODLY, as ``cko_max`` and ``cko_min`` (see :doc:`part`).

The data port is constrained with input delays: the clock trace, the part's clock to out and the data trace (see :doc:`generate`).
For the DAC81404 example, the read clock ``dac_sclk_rd`` runs at 80 ns, as the part's ``SDO`` allows 12.5 MHz at most:

.. code-block:: text

   setup (max) input delay = clock trace max + cko_max + data trace max = 3 + 30 + 1 = 34 ns
   hold (min) input delay  = clock trace min + cko_min + data trace min = 1 +  0 + 0 =  1 ns

Launch edge 2 at 80 ns is captured by edge Y at 120 ns, a setup requirement of 40 ns.
The hold edge I, at 40 ns, gives a hold requirement of -40 ns: the next bit, launched at 160 ns, must not reach the device before edge Y.

.. code-block:: toml

   [[port]]
   name = "I_DAC_DATA"
   methodology = "SDR-SS-RT-DI"
   launch_clock = {name = "dac_sclk_rd", setup_edge = 2, hold_edge = 2}
   capture_clock = {name = "clk_100mhz", setup_edge = "Y", hold_edge = "I"}

The edges are drawn with the launch clock on top, as for SDR-SS-O, and the drawing ends at the edge of the forwarded clock after the last edge of the port.
The capture edges are chosen to match the design: they must be the clock cycle on which the device samples the data.
In the example, Y samples the data near the start of the time it is valid, so the setup slack is small and the hold slack large.
Edges in the middle of that time would make the interface more robust.

A timing report of a round trip runs from the launch clock to the capture register:

.. code-block:: text

   launch clock path -> clock port -> input delay -> data port -> capture register

The launch clock path runs through the device to the clock port, as ``-reference_pin`` makes it, and the input delay starts there.
So the rules check that the launch clock path ends at the clock port, and the data path starts at the data port: together they show the whole clock path to the pin is included, and the right input port is timed.

These rules are checked on the timing reports of each SDR-SS-RT-DI port:

=======  =====================  ==================================================================
Stage    Rule                   Checks
=======  =====================  ==================================================================
0        s0_timing_report_001   A setup timing report exists at each process corner.
0        s0_timing_report_002   A hold timing report exists at each process corner.
0        s0_trace_001           A data trace from the part and its clock trace connect the port.
0        s0_data_path_002       The data path starts at the port.
0        s0_clock_path_002      The launch clock path ends at the launch clock's port.
1        s1_clock_001           The launch and capture clock paths start at the same point.
2        s2_clock_001           The launch clock path is the same in every timing report.
2        s2_clock_002           The capture clock path is the same in every timing report.
2        s2_data_path_001       The data path is the same in every timing report.
2        s2_input_delay_001     The input delay is the same in every setup timing report.
2        s2_input_delay_002     The input delay is the same in every hold timing report.
3        s3_input_delay_001     The maximum input delay matches the calculated input delay.
3        s3_input_delay_002     The minimum input delay matches the calculated input delay.
4        s4_capture_clock_001   The capture clock name matches the interface.
4        s4_capture_clock_002   The capture clock period matches the interface.
4        s4_launch_clock_001    The launch clock name matches the interface.
4        s4_launch_clock_002    The launch clock period matches the interface.
4        s4_part_002            The launch clock edge is the edge type the part launches on.
4        s4_requirement_001     The setup requirement is the time between the setup edges.
4        s4_requirement_002     The hold requirement is the time between the hold edges.
5        s5_slack_001           Setup slack is not negative.
5        s5_slack_002           Hold slack is not negative.
=======  =====================  ==================================================================

The timing tool reports a round trip from launch edge 0, such as ``dac_sclk_rd rise@0.000ns`` to ``clk_100mhz rise@40.000ns``, rather than from the configured edges 2 and Y.
The requirement is the same, so s4_requirement_001 and s4_requirement_002 compare the requirements, not the edges.

Methodologies stacv generates constraints for
---------------------------------------------

These methodologies are written from the device's view in the interface file.
``stacv generate`` writes their constraints and report script; ``stacv check`` has no rules for them yet.

==============  ==================================================================  ===================  ===============
Methodology     The device...                                                       Clock comes from     Part pin
==============  ==================================================================  ===================  ===============
SDR-SS-I        captures data the part sends with its clock                          the part             SDR-SS-O
SDR-SS-RT-DO    sends data on a clock the part sends, for the part to capture        the part             SDR-SS-RT-DI
SDR-SYS-O       sends data; a clock source drives the device and the part            a clock source       SDR-SYS-I
SDR-SYS-I       captures data; a clock source drives the device and the part         a clock source       SDR-SYS-O
DDR-SS-O        sends data on both edges of a clock it forwards                      the device           DDR-SS-I
DDR-SS-I        captures data the part sends on both edges of its clock              the part             DDR-SS-O
==============  ==================================================================  ===================  ===============

A round trip is named by where its data ends: SDR-SS-RT-DI when the data comes back to whoever supplies the clock, SDR-SS-RT-DO when the clock is received and data is returned.
Part files use the part's view and interface files the device's, so the same round trip has one name in each.

A clock from the part, or from a clock source, enters the device on a port and is created there; a forwarded clock is generated where the device generates it.
The delays are measured from the clock at the device's clock port:

* clock from the part: input delay = part clock to out + data trace - clock trace; output delay = data trace + part setup + clock trace (minimums with the hold and the other trace limits).
* clock from a source: the part's clock edge comes the difference of the two clock traces after the device's, which is added to the input delay and subtracted from the output delay.
* double data rate: the delays are written for the rising edges, and again for the falling edges with ``-clock_fall -add_delay``.

The VSC8540ET example, in ``example/microchip/vsc8540et``, uses every one of them, with a VHDL design to run through Vivado.
