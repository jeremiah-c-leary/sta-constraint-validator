Methodologies
=============

A methodology defines how to perform a timing analysis a single signal between devices.
These methodologies are defined relative to the device being timed.

The following represent a subset of named methodologies:

* Single Data Rate (SDR) Source Synchronous (SS) Output (SDR-SS-O)
* SDR SS Round Trip (SDR-SS-RT)
* SDR SS Input (SDR-SS-I)
* Double Data Rate (DDR) SS Output (DDR-SS-O)
* DDR SS Input (DDR-SS-I)

An interface, such as SPI, could use more than one methodology.
For example, an SPI interface to a DAC could use:

* SDR-SS-O for MOSI and CS_F
* SDR-SS-RT for MISO

An interface is considered fully timed when the methodology of each pin is validated.

The part defines the methodology of each of its pins.
The pins are grouped into interfaces, and a part can have more than one interface.
The methodology names are relative to the device, even in the part:
a part input pin, which the device drives, uses an output methodology such as SDR-SS-O.

Each interface is timed independently, with its own board data.
The traces in the board data connect each pin of the part interface to a device port.
Those device ports determine which timing reports the methodology needs.
If a device connects to two of the same part, each connection is a separate interface with its own board data.

A device port shared by two interfaces, such as a shared SPI bus, is not supported yet.
Each interface would calculate its own output delay for the shared port, but the timing reports carry only one.

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
The part's setup and hold requirements, and the board delays, are given to the timing tool as output delays.
stacv calculates the output delays itself and checks that the timing reports use them.

Information sources
^^^^^^^^^^^^^^^^^^^

Each source provides only the information it knows:

==============  =================================================================  ==============================
Source          Provides                                                           Example
==============  =================================================================  ==============================
Part            The pins of the interface and the methodology of each pin.         ``SDIN``: SDR-SS-O
Part            The clock pin each data pin is referenced to.                      ``SCLK``
Part            The setup and hold of each data pin, and the clock edge they       5 ns, 5 ns on the falling edge
                apply to (:doc:`part`).
Board data      The trace from each part pin to a device port, and its delays      ``SDIN`` to ``O_DAC_DATA``
                (:doc:`board_data`).
Device          The launch clock and its frequency.                                ``clk_100mhz``, 100 MHz
Device          The capture clock and its frequency.                               ``dac_sclk``, 20 MHz
Device          The setup and hold launch and capture edges of each port.          8, C and 0, A
Device          The process corners (:doc:`device`).                               Slow, Fast
Timing reports  What the timing tool timed.
==============  =================================================================  ==============================

The data ports and the clock port are not listed by the user.
They are found by following the traces from the part pins:

* the data ports are the device ports connected to the part's SDR-SS-O data pins
* the clock port is the device port connected to the part clock pin

The user does not provide the output delays.
They are calculated from the part and the board data (see `Output delay calculation`_).

Clock edges
"""""""""""

The launch and capture edges are the most important information the user provides.
A timing report only proves timing is met if it times the intended edges.
A timing report that meets timing on the wrong edges is not valid.

The user states which edges are intended, not the time of each edge.
stacv reads the edge times from each timing report and checks that they are the intended edges.

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
stacv checks that the edges given for the part clock are of that type (``s3_part_002``).

.. code-block:: text

                 0    1    2    3    4    5    6    7    8    9    10
                 +----+    +----+    +----+    +----+    +----+    +--
   clk_100mhz    |    |    |    |    |    |    |    |    |    |    |
              ---+    +----+    +----+    +----+    +----+    +----+

                 A                        B                        C
                 +------------------------+                        +--
   dac_sclk      |                        |                        |
              ---+                        +------------------------+

   time          0         10        20        30        40        50 ns

In this example, the setup check launches on edge 8 and captures on edge C.
The hold check launches on edge 0 and captures on edge A.

Output delay calculation
""""""""""""""""""""""""

An output delay in the timing constraints must account for the part's setup and hold requirements and the board trace delays.
If the user provided the output delays, stacv would only check that the same number was typed twice.
Instead, stacv calculates the output delays and checks them against the timing reports.

Each trace in the board data connects a part pin to a device port.
The ``device_pin`` of a trace is the port name as it appears in the timing reports.
For each SDR-SS-O data pin of the part interface, stacv finds:

* the data trace: the trace whose part pin is the data pin; its device pin is the data port
* the clock trace: the trace whose part pin is the clock pin of the data pin; its device pin is the clock port
* the setup and hold of the data pin, from the part

.. code-block:: text

   Device                Board                  Part
   O_DAC_DATA  ------- data trace -------->  SDIN   setup and hold relative to SCLK
   O_DAC_SCLK  ------- clock trace ------->  SCLK

The output delays are:

.. code-block:: text

   setup (max) output delay = setup of the data pin + data trace max delay - clock trace min delay
   hold (min) output delay  = data trace min delay - clock trace max delay - hold of the data pin

The calculation fails if:

* a pin of the part interface has no trace (``s3_trace_001``)
* a part data pin is not referenced to a clock pin of its interface (``s3_part_001``)

Matching timing reports
^^^^^^^^^^^^^^^^^^^^^^^

The data ports are found from the part and the board data (see `Information sources`_).
A timing report belongs to a data port when its destination is that data port.

.. code-block:: text
   :emphasize-lines: 4

   Slack (MET) :             0.272ns  (arrival time - required time)
     Source:                 q_spi_output_data_reg/C
                               (rising edge-triggered cell FDCE clocked by clk_100mhz  {rise@0.000ns fall@5.000ns period=10.000ns})
     Destination:            O_DAC_DATA
                               (output port clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=50.000ns})

Only the destination is used to match.
The launch clock, capture clock and clock port are checked by rules after matching.
A report with the wrong capture clock is then reported as a rule violation that names the clock, instead of a missing report.

A timing report whose destination is not a listed data port is not matched to this methodology.
A timing report that matches no methodology is a failure (``s4_timing_report_001``).

Required timing reports
^^^^^^^^^^^^^^^^^^^^^^^

The process corners are listed in the device definition (see :doc:`device`).
Each timing report states the process corner it was timed at.

Each data port must have at least one setup and one hold timing report at each process corner.
With slow and fast process corners, each data port needs at least four timing reports:

=======  ====  ====
Corner   Max   Min
=======  ====  ====
Slow     X     X
Fast     X     X
=======  ====  ====

Max timing reports are setup checks and min timing reports are hold checks.
A data port can have more than one timing report per corner, for example one for each source register.
Every matched timing report is checked.

Rules
^^^^^

These rules are checked on the timing reports matched to each data port.
The stages run in order, as described in :doc:`trc`.

=======  =====================  ==================================================================
Stage    Rule                   Checks
=======  =====================  ==================================================================
1        s1_clock_001           Launch and capture clock paths start at the same point.
2        s2_clock_001           Launch clock paths match across timing reports.
2        s2_clock_002           Capture clock paths match across timing reports.
2        s2_data_path_001       Data paths match across timing reports.
2        s2_output_delay_001    Output delays match across timing reports of the same type.
3        s3_trace_001           Every pin of the part interface has a trace in the board data.
3        s3_part_001            Every part data pin is referenced to a clock pin of its interface.
3        s3_part_002            Edges at the part clock are the edge type the part requires.
3        s3_output_delay_001    Output delays match the calculated output delays.
4        s4_process_corner_001  A setup and hold timing report exists at each process corner.
4        s4_process_corner_002  Every timing report is at a listed process corner.
4        s4_timing_report_001   Every timing report matches a data port of a methodology.
4        s4_data_path_001       Data path ends at the data port.
4        s4_clock_path_001      Capture clock path ends at the clock port.
4        s4_launch_clock_001    Launch clock name matches the information provided.
4        s4_launch_clock_002    Launch clock frequency matches the information provided.
4        s4_capture_clock_001   Capture clock name matches the information provided.
4        s4_capture_clock_002   Capture clock frequency matches the information provided.
4        s4_launch_edge_001     Launch edges match the information provided.
4        s4_capture_edge_001    Capture edges match the information provided.
5        s5_slack_001           Setup slack is not negative.
5        s5_slack_002           Hold slack is not negative.
=======  =====================  ==================================================================

Results
^^^^^^^

stacv reports the methodology for each port, with the rules checked and the result of each.

.. code-block:: text

   Interface: DAC81404 SPI
     Port: O_DAC_DATA                                  PASS
       Methodology: SDR-SS-O (clock port O_DAC_SCLK)
         Timing reports: 4 (setup slow, setup fast, hold slow, hold fast)
         s1_clock_001          PASS
         s2_clock_001          PASS
         ...
         s5_slack_002          PASS
     Port: O_DAC_CSF                                   PASS
       Methodology: SDR-SS-O (clock port O_DAC_SCLK)
         Timing reports: 4 (setup slow, setup fast, hold slow, hold fast)
         s1_clock_001          PASS
         s2_clock_001          PASS
         ...
         s5_slack_002          PASS

For CI/CD, each interface is a JUnit testsuite and each data port of a methodology is a testcase.
A failing rule is a failure in that testcase and names the timing report file and line.
Timing reports that match no data port are reported in a separate ``unmatched timing reports`` testcase of the interface.

Example input
^^^^^^^^^^^^^

This is a minimal input for this methodology only.
It shows the part, board data and device information for the DAC81404 serial interface.
It will be replaced once more methodologies are supported.

.. code-block:: yaml

   part:
     vendor: Texas Instruments
     name: DAC81404
     interface:
       - serial_interface:
           clock:
             - SCLK:
                 max_freq: 50 MHz
           data:
             - SDIN:
                 methodology: sdr_ss_o
                 clock: SCLK
                 falling_edge:
                   setup:
                     id: tSDIS
                     value: 5 ns
                   hold:
                     id: tSDIH
                     value: 5 ns

   board:
     trace:
       - data_out:
           device_pin: O_DAC_DATA
           part_pin: SDIN
           delay:
             max: 2.5
             min: 1.5
       - clock:
           device_pin: O_DAC_SCLK
           part_pin: SCLK
           delay:
             max: 2.0
             min: 1.0

   device:
     vendor: AMD
     name: ZU19EG
     process_corners:
       - Slow
       - Fast
     interface:
       - DAC_DATA_INTF:
           clock:
             - clk_100mhz:
                 frequency: 100 MHz
             - dac_sclk:
                 frequency: 20 MHz
           data:
             output:
               - O_DAC_DATA:
                   launch_clock:
                     name: clk_100mhz
                     edge:
                       setup: 8
                       hold: 0
                   capture_clock:
                     name: dac_sclk
                     edge:
                       setup: C
                       hold: A

   timing_reports:
     - timing_reports/O_DAC_DATA_timing.rpt

