.. The concept only, independent of stacv's commands and file formats and of any timing tool's commands; the worked
   example shows how stacv and the timing tool do each step.  Sections marked (DID) are the ones the DID repeats for each
   port, with that port's values.

Single Data Rate Source Synchronous Output to the First and Last Clock (SDR-SS-O-FLC)
=====================================================================================

Intent
------

Some signals are not timed to every edge of their clock, but to the first and last edges of a clock that stops between transfers.
A chip select is the usual example: the device sets it before a transfer and clears it after, and the clock runs only in between.
Its setup is to the first clock edge after it is set, and its hold is from the last clock edge before it is cleared.

The device sends the signal together with the clock the part captures it with, from the same clock, so what is timed is the difference between their paths, as for any source synchronous signal.

A timing tool assumes every clock runs all the time.
It cannot see that the clock stops, so it times the signal against the clock edges either side of each change, as if the clock ran between transfers.
The edges are chosen so that those checks are the first and last edges of a transfer.

Applies to
----------

* An output that is set before a transfer and cleared after it.
* The part captures it against the first and last edges of its clock pin, on the rising edge or the falling edge.
* The device generates that clock from the clock that launches the signal, with an element such as a register that divides it, or a DDR output cell, and stops it between transfers.

Architecture  (DID)
-------------------

.. code-block:: text

     Device                                                       Part
   +---------------------------------------------------+        +---------------------+
   |                                                   |   cs   |                     |
   |  launch --+--> [chip select register] -----------[X]----->[X] chip select pin    |
   |  clock    |                     chip select port  |  trace |                     |
   |           |                                       |        |                     |
   |           |                                       |  clock |                     |
   |           +--> [clock element] ------------------[X]----->[X] clock pin          |
   |                                       clock port  |  trace |                     |
   |                                                   |        |                     |
   +---------------------------------------------------+        +---------------------+

The launch clock drives two elements:

* the **chip select register**, which launches the chip select to its port, and
* the **clock element**, which generates the forwarded clock and sends it to the clock port.

From there, a trace on the board takes each to the part.
Two paths are timed against each other:

* the **chip select path**: from the launch clock, through the chip select register, its port and its trace, to the part's chip select pin;
* the **forwarded clock path**: from the launch clock, through the clock element, the clock port and the clock trace, to the part's clock pin.

The examples on this page time the chip select of the Texas Instruments DAC81404, CSF, driven by the device's port O_DAC_SDEN_F.
The clock edges and the part's setup and hold are the DAC81404's, from its datasheet; the trace delays are example values.

For O_DAC_SDEN_F:

=====================  =========================
Element                O_DAC_SDEN_F
=====================  =========================
Launch clock           clk_100mhz
Chip select register   q_spi_sden_f_reg
Chip select port       O_DAC_SDEN_F
Clock element          q_spi_output_clock_reg
Clock port             O_DAC_SCLK
Part chip select pin   CSF
Part clock pin         SCLK
=====================  =========================

Information needed  (DID)
-------------------------

Each piece of information comes from the person who knows it.
The steps refer to each by its ID.

=====  ==============================================================================  ==============  =================================
ID     Information                                                                     Who knows it    O_DAC_SDEN_F
=====  ==============================================================================  ==============  =================================
I1     The launch clock and its period                                                 designer        clk_100mhz, 10 ns
I2     The register that launches the chip select                                      designer        q_spi_sden_f_reg
I3     The element that generates the forwarded clock, and its divide                  designer        q_spi_output_clock_reg, 4
I4     The forwarded clock's period, and the port it leaves the device on              designer        40 ns, O_DAC_SCLK
I5     The level the forwarded clock idles at between transfers                        designer        low
I6     The edge of its clock the part captures on                                      part datasheet  falling
I7     The part's setup to the first edge, and hold from the last edge                 part datasheet  tCSS 30 ns, tCSH 10 ns
I8     The chip select trace's maximum and minimum delay                               HW engineer     1 ns, 0 ns
I9     The clock trace's maximum and minimum delay                                     HW engineer     3 ns, 1 ns
I10    The launch and capture edges for setup, and the launch and capture edges        designer        setup 4 to 3, hold 8 to 1
       for hold
=====  ==============================================================================  ==============  =================================

Steps  (DID)
------------

1. Choose the launch and capture edges  (I1, I2, I4, I5, I6, I10)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every edge of each clock is counted from 0 ns, rising and falling in turn.
Each clock's edges are numbered from 0 on that clock: 0, 1, 2, ..., the even ones rising and the odd ones falling.
Even numbers are rising edges.

The chip select changes twice: once when it is set, before the transfer, and once when it is cleared, after it.
Its setup comes from the launch edge that sets it, and its hold from the launch edge that clears it, so the two launch edges are independent: each can be moved without moving the other.

* The setup check times the chip select, set on one launch edge, against the first capture edge of the transfer.
* The hold check times the chip select, cleared on another launch edge, against the last capture edge of the transfer.

The part captures on one kind of edge only (I6), so both capture edges are of that kind.
The edges are drawn in two windows, so they can be compared with the datasheet's figure: the clock idle (I5) up to its first pulse, with the first edge; and the clock idle after its last pulse, with the last edge.

For O_DAC_SDEN_F, captured on the falling edges of dac_sclk, which idles low:

.. code-block:: text

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                            |---------------setup requirement-------------->|
                                                  clock starts ---->|

                                                                    2_______________________3
   dac_sclk       __________________________________________________|                       |
   (25 MHz)

   setup requirement = 40 ns

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                            |<---hold requirement---|
                           clock stops ---->|

                    0_______________________1
   dac_sclk       __|                       |________________________________________________
   (25 MHz)

   hold requirement = -20 ns

* setup: launch 4 at 20 ns, capture 3 at 60 ns, the first falling edge, a setup requirement of 40 ns;
* hold: launch 8 at 40 ns, capture 1 at 20 ns, the last falling edge before it, a hold requirement of -20 ns.

"clock starts" marks the edge the clock starts running on, the first edge of its first pulse, and "clock stops" the edge it stops on, the last edge of its last pulse.
The setup and hold are to the capture edges, 3 and 1: the clock starts on 2, and the first edge the part captures on is 3.

2. Create the forwarded clock  (I1, I3, I4, I5)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The forwarded clock is a clock of its own, generated from the launch clock.
It is created where it is generated: at the output of the clock element, from the launch clock at the element's clock input, divided as the element divides it.

Created there, the forwarded clock starts at the same point as the chip select does, at a register's output, and the timing tool times its path from the element to the clock port just as it times the chip select's path from its register to its port.
The two paths are timed alike, from the same launch clock, so their difference is what the timing shows.

Between transfers the clock stops at its idle level (I5); the timing tool does not model the stop, which is why the edges of step 1 pick the first and last edges of a transfer.

For O_DAC_SDEN_F, the forwarded clock dac_sclk is created at the output of q_spi_output_clock_reg, from clk_100mhz at its clock input, divided by 4: 40 ns / 10 ns.

3. Calculate the output delays  (I7, I8, I9)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The part needs the chip select to be set its setup time before the first clock edge, and to stay set its hold time after the last.
The output delays move those requirements from the part's pins back to the device's pins, so the timing tool can time them at the device.

The output delays are against the forwarded clock at the device's clock port, as the part sees it, so the clock's path from the element to the port is part of the timing.

.. code-block:: text

   maximum output delay  =  part setup  +  chip select trace maximum  -  clock trace minimum
   minimum output delay  =  chip select trace minimum  -  clock trace maximum  -  part hold

The maximum output delay is the setup check.
It is the worst case for setup: the chip select is as late as it can be, so its trace is at its maximum, and the clock is as early as it can be, so its trace is at its minimum.
The chip select must be set that much before the first clock edge leaves the device.

The minimum output delay is the hold check.
It is the worst case for hold: the chip select is as early as it can be, at its trace's minimum, and the clock as late as it can be, at its trace's maximum.
The part's hold is subtracted: the chip select must stay set that long after the last clock edge, so it may be cleared no earlier than this.

For O_DAC_SDEN_F:

.. code-block:: text

   maximum output delay  =  30  +  1  -   1  =   30 ns
   minimum output delay  =   0  -  3  -  10  =  -13 ns

4. Set the multicycle paths  (I10)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Left to itself, a timing tool times each path on the closest edges: for setup, the launch edge closest before a capture edge, and for hold, the edges that check the setup's capture edge is not disturbed by the next launch.
These are not the edges intended.
The chip select register is clocked by the launch clock, but the chip select changes only twice in a transfer, so the setup and hold requirements can be moved to the edges that set and clear it.

The part captures on the falling edges of dac_sclk, 1 and 3 (I6), so every capture edge below is one of them.

**The default edges.**  For setup, the closest launch edge before the first capture edge 3 is 10, at 50 ns: a setup requirement of 10 ns.
For hold, the next launch edge, 12 at 60 ns, against the same 3: a hold requirement of 0 ns.

.. code-block:: text

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                                                                |---------->| setup requirement
                                                  clock starts ---->|

                                                                    2_______________________3
   dac_sclk       __________________________________________________|                       |
   (25 MHz)

   setup requirement = 10 ns

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                                                                            | hold requirement
                                                                           clock stops ---->|

                    0_______________________1                       2_______________________3
   dac_sclk       __|                       |_______________________|                       |
   (25 MHz)

   hold requirement = 0 ns

**Moving the setup edge.**  A setup multicycle path of 4, counted in launch clock periods, moves the setup launch three periods earlier, to edge 4, which sets the chip select: a setup requirement of 40 ns.
The hold check moves with it, to the launch edge after the new setup launch edge, 6 to 3: a hold requirement of 30 ns.
That hold check times the chip select launched on edge 6, which does not change it, so it is not the intended check.

.. code-block:: text

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                            |---------------setup requirement-------------->|
                                                  clock starts ---->|

                                                                    2_______________________3
   dac_sclk       __________________________________________________|                       |
   (25 MHz)

   setup requirement = 40 ns

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                                        |---------hold requirement--------->|
                                                                           clock stops ---->|

                    0_______________________1                       2_______________________3
   dac_sclk       __|                       |_______________________|                       |
   (25 MHz)

   hold requirement = 30 ns

**Moving the hold edge back.**  The hold check belongs on the last capture edge before the chip select is cleared, 1, from the launch edge that clears it, 8.
A hold multicycle path of 5 moves the hold check back five launch periods, 50 ns: its requirement goes from 30 ns to -20 ns.

.. code-block:: text

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                            |---------------setup requirement-------------->|
                                                  clock starts ---->|

                                                                    2_______________________3
   dac_sclk       __________________________________________________|                       |
   (25 MHz)

   setup requirement = 40 ns

                                                                                1     1     1
                    0_____1     2_____3     4_____5     6_____7     8_____9     0_____1     2
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)
                                            |<---hold requirement---|
                           clock stops ---->|

                    0_______________________1
   dac_sclk       __|                       |________________________________________________
   (25 MHz)

   hold requirement = -20 ns

In general:

.. code-block:: text

   setup multicycle  =  setup requirement / launch period
   hold multicycle   =  (setup requirement - hold requirement) / launch period - 1

For O_DAC_SDEN_F: a setup multicycle of 40 / 10 = 4, and a hold multicycle of (40 - -20) / 10 - 1 = 5.

See also
--------

* :doc:`../spi`, which uses this methodology for CS.
* The overview of the methodologies: :doc:`../methodology`.
