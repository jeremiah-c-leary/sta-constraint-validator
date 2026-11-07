:orphan:

.. DRAFT - not for publishing yet.  The concept only, independent of stacv's commands and file formats and of any
   timing tool's commands; the worked example (sdr_ss_o_example.rst) shows how stacv and the timing tool do each step.
   Sections marked (DID) are the ones the DID repeats for each port, with that port's values.
   Tabled: an Assumptions section (the rules, generated from the methodology class, and what the reports cannot show).

Single Data Rate Source Synchronous Output (SDR-SS-O)
=====================================================

Intent
------

The device sends data to the part together with the clock the part captures it with.
Both leave the device from the same clock, so they start together, and travel to the part side by side.

This is what makes an interface source synchronous: the clock comes from the source of the data.
Whatever delays the clock and the data share cancel out, so what is timed is the difference between the two: how much later, or earlier, the data reaches the part than its clock.

Applies to
----------

* An output port, whose data changes once in each period of the clock it is captured with.
* The part captures the data on one edge of its clock pin: the rising edge, or the falling edge.
* The device generates that clock from the clock that launches the data, with an element such as a register that divides it, or a DDR output cell that forwards it at the same frequency.

Architecture  (DID)
-------------------

.. code-block:: text

     Device                                                 Part
   +---------------------------------------------+        +---------------------+
   |                                             |  data  |                     |
   |  launch --+--> [data register] ------------[X]----->[X] data pin           |
   |  clock    |                     data port   |  trace |                     |
   |           |                                 |        |                     |
   |           |                                 |  clock |                     |
   |           +--> [clock element] ------------[X]----->[X] clock pin          |
   |                                 clock port  |  trace |                     |
   |                                             |        |                     |
   +---------------------------------------------+        +---------------------+

The launch clock drives two elements:

* the **data register**, which launches the data to the data port, and
* the **clock element**, which generates the forwarded clock and sends it to the clock port.

From there, a trace on the board takes each to the part.
Two paths are timed against each other:

* the **data path**: from the launch clock, through the data register, the data port and the data trace, to the part's data pin;
* the **forwarded clock path**: from the launch clock, through the clock element, the clock port and the clock trace, to the part's clock pin.

The examples on this page time the data input of the Texas Instruments DAC81404, SDIN, driven by the device's port O_DAC_DATA.
The clock edges and the part's setup and hold are the DAC81404's, from its datasheet; the trace delays are example values.

For O_DAC_DATA:

=================  =========================
Element            O_DAC_DATA
=================  =========================
Launch clock       clk_100mhz
Data register      q_spi_output_data_reg
Data port          O_DAC_DATA
Clock element      q_spi_output_clock_reg
Clock port         O_DAC_SCLK
Part data pin      SDIN
Part clock pin     SCLK
=================  =========================

Information needed  (DID)
-------------------------

Each piece of information comes from the person who knows it.
The steps refer to each by its ID.

=====  =====================================================================  ==============  ===============================
ID     Information                                                            Who knows it    O_DAC_DATA
=====  =====================================================================  ==============  ===============================
I1     The launch clock and its period                                        designer        clk_100mhz, 10 ns
I2     The register that launches the data                                    designer        q_spi_output_data_reg
I3     The element that generates the forwarded clock, and its divide         designer        q_spi_output_clock_reg, 4
I4     The forwarded clock's period, and the port it leaves the device on     designer        40 ns, O_DAC_SCLK
I5     The edge of its clock the part captures on                             part datasheet  falling
I6     The part's setup and hold                                              part datasheet  10 ns, 10 ns
I7     The data trace's maximum and minimum delay                             HW engineer     3 ns, 1 ns
I8     The clock trace's maximum and minimum delay                            HW engineer     3 ns, 1 ns
I9     The launch and capture edges, for setup and for hold                   designer        setup 8 to D, hold 8 to B
=====  =====================================================================  ==============  ===============================

Steps  (DID)
------------

1. Choose the launch and capture edges  (I1, I2, I4, I5, I9)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every edge of each clock is counted from 0 ns, rising and falling in turn.
The launch clock's edges are numbered, 0, 1, 2, ..., and the capture clock's are lettered, A, B, C, ....
Even numbers, and A, C, E, ..., are rising edges.

The setup check times the data launched on one edge against the capture edge that should capture it.
The hold check times the same data against the capture edge before it, the one that captured the previous data, which the new data must not disturb.
That edge is the capture edge of the same kind before the setup capture edge: the part captures on one kind of edge only (I5).

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

The setup requirement is the time from the setup launch edge to the setup capture edge, and the hold requirement the time from the hold launch edge to the hold capture edge.

For O_DAC_DATA, the data is launched on edge 8, at 40 ns, at the same time as the rising edge C of the forwarded clock:

* setup: launch 8 at 40 ns, capture D at 60 ns, a setup requirement of 20 ns;
* hold: launch 8 at 40 ns, capture B at 20 ns, a hold requirement of -20 ns.

2. Create the forwarded clock  (I1, I3, I4)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The forwarded clock is a clock of its own, generated from the launch clock.
It is created where it is generated: at the output of the clock element, from the launch clock at the element's clock input, divided as the element divides it.

Created there, the forwarded clock starts at the same point as the data does, at a register's output, and the timing tool times its path from the element to the clock port just as it times the data's path from its register to the data port.
The two paths are timed alike, from the same launch clock, so their difference is what the timing shows.

For O_DAC_DATA, the forwarded clock dac_sclk is created at the output of q_spi_output_clock_reg, from clk_100mhz at its clock input, divided by 4: 40 ns / 10 ns.

3. Calculate the output delays  (I6, I7, I8)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The part needs the data to arrive its setup time before its clock edge, and to stay its hold time after it.
The output delays move those requirements from the part's pins back to the device's pins, so the timing tool can time them at the device.

The output delays are against the forwarded clock at the device's clock port, as the part sees it, so the clock's path from the element to the port is part of the timing.

.. code-block:: text

   maximum output delay  =  part setup  +  data trace maximum  -  clock trace minimum
   minimum output delay  =  data trace minimum  -  clock trace maximum  -  part hold

The maximum output delay is the setup check.
It is the worst case for setup: the data is as late as it can be, so its trace is at its maximum, and the clock is as early as it can be, so its trace is at its minimum.
The data must leave the device that much before the clock edge.

The minimum output delay is the hold check.
It is the worst case for hold: the data is as early as it can be, at its trace's minimum, and the clock as late as it can be, at its trace's maximum.
The part's hold is subtracted: the data must stay that long after the clock edge, so it may change no earlier than this.

For O_DAC_DATA:

.. code-block:: text

   maximum output delay  =  10  +  3  -   1  =   12 ns
   minimum output delay  =   1  -  3  -  10  =  -12 ns

4. Set the multicycle paths  (I9)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Left to itself, a timing tool times each path on the closest edges: for setup, the launch edge closest before a capture edge, and for hold, the edges that check the setup's capture edge is not disturbed by the next launch.
These are rarely the edges intended.
The data register is clocked by the launch clock, but the data changes only once in each period of the forwarded clock: of the four launch edges in each period of dac_sclk, only edge 8, with C, launches data.
So the setup and hold requirements can be moved to the edges that time the data as it is launched.

The part captures on the falling edges of dac_sclk, B and D (I5), so every capture edge below is one of them.

**The default edges.**  For setup, the closest launch edge before the capture edge D is 10, at 50 ns: a setup requirement of 10 ns.
For hold, the next launch edge, 12 at 60 ns, against the same D: a hold requirement of 0 ns.

.. code-block:: text

                                                                                1     1     1     1     1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                                                                |---------->| setup requirement
                                                                                            | hold requirement

                    A_______________________B                       C_______________________D                       E
   dac_sclk       __|                       |_______________________|                       |_______________________|
   (25 MHz)


   setup requirement = 10 ns
   hold requirement = 0 ns

**Moving the setup edge.**  A setup multicycle path of 2, counted in launch clock periods, moves the setup launch one period earlier, to edge 8: a setup requirement of 20 ns.
The hold check moves with it, to the launch edge after the new setup launch edge, 10 to D: a hold requirement of 10 ns.
That hold check times data launched on edge 10, which does not launch data, so it is not the intended check.

.. code-block:: text

                                                                                1     1     1     1     1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2_____3     4_____5     6
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                                                    |---setup requirement-->|
                                                                                |---------->| hold requirement

                    A_______________________B                       C_______________________D                       E
   dac_sclk       __|                       |_______________________|                       |_______________________|
   (25 MHz)


   setup requirement = 20 ns
   hold requirement = 10 ns

**Moving the hold edge back.**  The hold check belongs on the capture edge before the setup capture edge, the falling edge that captured the previous data.
With the setup check now from edge 8 to D, the hold check is from edge 8 to B.
A hold multicycle path of 3 moves the hold check back three launch periods, 30 ns: its requirement goes from 10 ns to -20 ns.

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

In general:

.. code-block:: text

   setup multicycle  =  setup requirement / launch period
   hold multicycle   =  (setup requirement - hold requirement) / launch period - 1

For O_DAC_DATA: a setup multicycle of 20 / 10 = 2, and a hold multicycle of (20 - -20) / 10 - 1 = 3.

See also
--------

* The worked example, which runs the timing reports, checks them, and lists the pitfalls: :doc:`sdr_ss_o_example`.
* :doc:`../spi`, which uses this methodology for COPI.
* The overview of the methodologies: :doc:`../methodology`.
