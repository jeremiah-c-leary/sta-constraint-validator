.. The concept only, independent of stacv's commands and file formats and of any timing tool's commands.
   Sections marked (DID) are the ones the DID repeats for each port, with that port's values.

Single Data Rate Source Synchronous Round Trip, Data In (SDR-SS-RT-DI)
======================================================================

Intent
------

The device sends the part a clock, the part launches data on that clock, and the device captures the data with its own clock, the clock the forwarded clock was generated from.

The timing is a round trip.
It runs out of the device through the clock port and the clock trace, through the part, which launches the data its clock to out after the clock edge, and back through the data trace and the data port to the register that captures the data.
The clock trace, the part's clock to out and the data trace all add up, so what is timed is when the data arrives back, against the device clock edge that captures it.

Applies to
----------

* An input whose data the part launches on a clock the device forwards to it.
* The part launches on one edge of its clock pin: the rising edge, or the falling edge.
* The device captures the data on the clock it generates the forwarded clock from, with an element such as a register that divides it, or a DDR output cell.

Architecture  (DID)
-------------------

.. code-block:: text

     Device                                                   Part
   +-----------------------------------------------+        +---------------------+
   |                                               |  clock |                     |
   |  device --+--> [clock element] --------------[X]----->[X] clock pin          |
   |  clock    |                       clock port  |  trace |      |              |
   |           |                                   |        |      | clock to out |
   |           |                                   |  data  |      v              |
   |           +--> [capture register] <----------[X]<-----[X] data pin           |
   |                                    data port  |  trace |                     |
   |                                               |        |                     |
   +-----------------------------------------------+        +---------------------+

The device clock drives two elements:

* the **clock element**, which generates the forwarded clock and sends it out of the clock port to the part, and
* the **capture register**, which captures the data that comes back on the data port.

There is one path, a round trip: from the device clock, through the clock element, the clock port and the clock trace to the part's clock pin; through the part, to its data pin, its clock to out later; and back through the data trace and the data port to the capture register.

The examples on this page time the data output of the Texas Instruments DAC81404, SDO, captured by the device on its port I_DAC_DATA.
The clock edges and the part's clock to out are the DAC81404's, from its datasheet; the trace delays are example values.

For I_DAC_DATA:

=================  =========================
Element            I_DAC_DATA
=================  =========================
Device clock       clk_100mhz
Clock element      q_spi_output_clock_reg
Clock port         O_DAC_SCLK
Part clock pin     SCLK
Part data pin      SDO
Data port          I_DAC_DATA
Capture register   q_spi_input_data_reg
=================  =========================

Information needed  (DID)
-------------------------

Each piece of information comes from the person who knows it.
The steps refer to each by its ID.

=====  =====================================================================  ==============  ==================================
ID     Information                                                            Who knows it    I_DAC_DATA
=====  =====================================================================  ==============  ==================================
I1     The device clock and its period                                        designer        clk_100mhz, 10 ns
I2     The register that captures the data                                    designer        q_spi_input_data_reg
I3     The element that generates the forwarded clock, and its divide         designer        q_spi_output_clock_reg, 8
I4     The forwarded clock's period, and the port it leaves the device on     designer        80 ns, O_DAC_SCLK
I5     The edge of its clock the part launches on                             part datasheet  rising
I6     The part's maximum and minimum clock to out                            part datasheet  tSDODLY 30 ns, 0 ns
I7     The clock trace's maximum and minimum delay                            HW engineer     3 ns, 1 ns
I8     The data trace's maximum and minimum delay                             HW engineer     1 ns, 0 ns
I9     The launch and capture edges, for setup and for hold                   designer        setup 2 to Y, hold 2 to I
=====  =====================================================================  ==============  ==================================

Steps  (DID)
------------

1. Choose the launch and capture edges  (I1, I2, I4, I5, I9)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Every edge of each clock is counted from 0 ns, rising and falling in turn.
The launch clock's edges are numbered, 0, 1, 2, ..., and the capture clock's are lettered, A, B, C, ....
Even numbers, and A, C, E, ..., are rising edges.

The launch edges are on the forwarded clock, where the part launches the data (I5), and the capture edges are on the device clock, where the capture register captures it.

* The setup check times the data launched on one edge of the forwarded clock against the device clock edge that captures it.
* The hold check times the same data against the device clock edge that captured the previous data, which the new data must not disturb.

The data comes back a whole round trip after its launch edge, so the capture edge is a choice: any device clock edge late enough for the data to have arrived, and early enough for the next data not to have.
Choose edges that meet timing first; moving them to centre the data, for the best margin, is a later step.

For I_DAC_DATA, launched on the rising edges of dac_sclk_rd and captured on clk_100mhz:

.. code-block:: text

                    0_______________________________________________1                                               2_______________________________________________3                                               4
   dac_sclk_rd    __|                                               |_______________________________________________|                                               |_______________________________________________|
   (12.5 MHz)
                                                                                                                    |---------------setup requirement-------------->|
                                                                    |<---------------hold requirement---------------|

                                                                                                                                                                                A     A     A     A     A     A     A
                    A_____B     C_____D     E_____F     G_____H     I_____J     K_____L     M_____N     O_____P     Q_____R     S_____T     U_____V     W_____X     Y_____Z     A_____B     C_____D     E_____F     G
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)


   setup requirement = 40 ns
   hold requirement = -40 ns

* setup: launch 2 at 80 ns, capture Y at 120 ns, a setup requirement of 40 ns;
* hold: launch 2 at 80 ns, capture I at 40 ns, a hold requirement of -40 ns.

2. Create the forwarded clock  (I1, I3, I4)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The forwarded clock is a clock of its own, generated from the device clock.
It is created where it is generated: at the output of the clock element, from the device clock at the element's clock input, divided as the element divides it.

Created there, the forwarded clock starts at a register's output, and the timing tool times its path from the element to the clock port, the first leg of the round trip.

For I_DAC_DATA, the forwarded clock dac_sclk_rd is created at the output of q_spi_output_clock_reg, from clk_100mhz at its clock input, divided by 8: 80 ns / 10 ns.

3. Calculate the input delays  (I6, I7, I8)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The input delay is the time from the forwarded clock's edge at the device's clock port to the data's arrival at the data port.
The clock travels out on its trace, the part launches the data its clock to out later, and the data travels back on its trace:

.. code-block:: text

   maximum input delay  =  clock trace maximum  +  part clock to out maximum  +  data trace maximum
   minimum input delay  =  clock trace minimum  +  part clock to out minimum  +  data trace minimum

The maximum input delay is the setup check: the data arrives as late as it can, with every part of the round trip at its longest.
The minimum input delay is the hold check: the data arrives as early as it can, with every part of the round trip at its shortest.

The input delays are against the forwarded clock at the device's clock port, so the clock's path from the element to the port is part of the timing.

For I_DAC_DATA:

.. code-block:: text

   maximum input delay  =  3  +  30  +  1  =  34 ns
   minimum input delay  =  1  +   0  +  0  =   1 ns

4. Set the multicycle paths  (I9)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Left to itself, a timing tool times each path on the closest edges: for setup, the first capture edge after the launch edge, and for hold, the capture edge before it.
The data comes back a whole round trip later, so these are rarely the edges intended.
Here the device clock captures, and it is the faster clock, so the multicycle paths are counted in its periods and move the capture edges.

**The default edges.**  For setup, the first device clock edge after launch 2 is S, at 90 ns: a setup requirement of 10 ns.
For hold, the device clock edge before it, Q at 80 ns: a hold requirement of 0 ns.

.. code-block:: text

                    0_______________________________________________1                                               2_______________________________________________3
   dac_sclk_rd    __|                                               |_______________________________________________|                                               |
   (12.5 MHz)
                                                                                                                    |---------->| setup requirement
                                                                                                                    | hold requirement

                    A_____B     C_____D     E_____F     G_____H     I_____J     K_____L     M_____N     O_____P     Q_____R     S_____T     U_____V     W_____X     Y
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)


   setup requirement = 10 ns
   hold requirement = 0 ns

**Moving the setup edge.**  A setup multicycle path of 4, counted in device clock periods, moves the setup capture three periods later, to Y: a setup requirement of 40 ns.
The hold check moves with it, to the device clock edge before Y, W at 110 ns: a hold requirement of 30 ns.
That hold check is against an edge that captures nothing from this interface, so it is not the intended check.

.. code-block:: text

                    0_______________________________________________1                                               2_______________________________________________3                                               4
   dac_sclk_rd    __|                                               |_______________________________________________|                                               |_______________________________________________|
   (12.5 MHz)
                                                                                                                    |---------------setup requirement-------------->|
                                                                                                                    |---------hold requirement--------->|

                                                                                                                                                                                A     A     A     A     A     A     A
                    A_____B     C_____D     E_____F     G_____H     I_____J     K_____L     M_____N     O_____P     Q_____R     S_____T     U_____V     W_____X     Y_____Z     A_____B     C_____D     E_____F     G
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)


   setup requirement = 40 ns
   hold requirement = 30 ns

**Moving the hold edge back.**  The hold check belongs on the device clock edge that captured the previous data, I at 40 ns, 80 ns before Y.
A hold multicycle path of 7 moves the hold capture back seven device clock periods, 70 ns: its requirement goes from 30 ns to -40 ns.

.. code-block:: text

                    0_______________________________________________1                                               2_______________________________________________3                                               4
   dac_sclk_rd    __|                                               |_______________________________________________|                                               |_______________________________________________|
   (12.5 MHz)
                                                                                                                    |---------------setup requirement-------------->|
                                                                    |<---------------hold requirement---------------|

                                                                                                                                                                                A     A     A     A     A     A     A
                    A_____B     C_____D     E_____F     G_____H     I_____J     K_____L     M_____N     O_____P     Q_____R     S_____T     U_____V     W_____X     Y_____Z     A_____B     C_____D     E_____F     G
   clk_100mhz     __|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|     |_____|
   (100 MHz)


   setup requirement = 40 ns
   hold requirement = -40 ns

In general, counted in capture clock periods:

.. code-block:: text

   setup multicycle  =  setup requirement / capture period
   hold multicycle   =  (setup requirement - hold requirement) / capture period - 1

For I_DAC_DATA: a setup multicycle of 40 / 10 = 4, and a hold multicycle of (40 - -40) / 10 - 1 = 7.

See also
--------

* :doc:`../spi`, which uses this methodology for CIPO.
* The overview of the methodologies: :doc:`../methodology`.
