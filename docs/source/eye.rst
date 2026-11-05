Eye Diagram
===========

``stacv visualize eye`` draws the eye of every analyzed port from its timing reports: the time its data is stable around the capture edge.
It reads the timing reports, so it is drawn after timing, with the part and traces files the delays come from.

.. code-block:: text

   stacv visualize eye interface.toml

A port meets timing when its slacks are not negative, but the slacks alone do not show how well the capture is placed.
The eye shows where the setup and hold window sits in the time the data is stable, and how the process corners move it.

Reading the eye
---------------

.. code-block:: text

   O_DAC_DATA (SDR-SS-O)
     setup 10 ns, hold 10 ns, 0.94 ns a character
                                                        setup slack  hold slack  offset from eye centre
       Slow  X........<----------|---------->........X     7.524 ns    7.438 ns               +0.043 ns
       Fast  XX.......<----------|---------->.......XX     7.260 ns    7.167 ns               +0.046 ns
       All   XX.......<----------|---------->.......XX     7.260 ns    7.167 ns               +0.046 ns

Each row is drawn from the capture edge at the endpoint: the part's pin for an output, and the capturing register for an input.

=========  ===============================================================================
Character  Meaning
=========  ===============================================================================
``|``      The capture edge.
``<``      Where the data must be stable from: the setup time before the edge.
``>``      Where the data must be stable until: the hold time after the edge.
``-``      The time between them, the setup and hold window.
``.``      The data is stable: the eye.
``X``      The data is changing, or outside the eye.
=========  ===============================================================================

A setup or hold time too short for a column, such as a register's library setup, is still drawn one column from the edge, as ``<|>``, so the reader can see it is there.
A setup or hold time of 0 has no mark, and a negative one puts its end of the window on the other side of the edge.

The heading gives the methodology, the setup and hold times, and the scale.
For an output, the setup and hold times are the part pin's; for an input, they are the register's library setup and hold, from its ``(Setup_...)`` and ``(Hold_...)`` rows in the timing reports.
The drawing is 40 columns wide, and runs from the earliest change to the latest over every row, so it ends at an ``X`` on both sides.

Rows
----

Each process corner is a row, drawn from its worst setup and worst hold timing report, over every bit of a bus and both edges of a double data rate clock.
The ``All`` row combines the corners: its slacks are the worst of every corner, so its eye is the time the data is stable at any corner.

The corners can move the eye.
O_MII_TX_EN, an SDR-SS-RT-DO output, is launched on a clock that comes in from the part, so the device's own delay is not cancelled, and changes with the corner:

.. code-block:: text

   O_MII_TX_EN (SDR-SS-RT-DO)
     setup 15 ns, hold 0 ns, 1.15 ns a character
                                                        setup slack  hold slack  offset from eye centre
       Slow  XXXXXX...........<------------|.........X    12.845 ns   10.336 ns               +1.255 ns
       Fast  X................<------------|....XXXXXX    18.400 ns    4.718 ns               +6.841 ns
       All   XXXXXX...........<------------|....XXXXXX    12.845 ns    4.718 ns               +4.064 ns

The eye of the fast corner is about 5.6 ns earlier than the slow corner's, so the ``All`` row leaves less of either.

Centring
--------

The best placement centres the setup and hold window in the eye, with equal setup and hold slack; the capture edge itself is at the centre only when the setup and hold times are equal.
``offset from eye centre`` is where the setup and hold window's centre is from the eye's:

.. code-block:: text

   offset = (setup slack - hold slack) / 2

A negative offset means the window is early in the eye, so the capture could move later by that much; a positive offset means it is late.
I_RGMII_RX_CTL is captured 5.5 ns early, so delaying its capture clock would centre it:

.. code-block:: text

   I_RGMII_RX_CTL (DDR-SS-I-SE)
     setup 0.011 ns, hold 0.191 ns, 0.54 ns a character
                                                        setup slack  hold slack  offset from eye centre
       Slow  XX.......<|>.......................XXXXXX     4.312 ns   13.139 ns               -4.413 ns
       Fast  XXXXXX...<|>...........................XX     2.102 ns   15.451 ns               -6.675 ns
       All   XXXXXX...<|>.......................XXXXXX     2.102 ns   13.139 ns               -5.518 ns

Calculation
-----------

All times are measured from the capture edge at the endpoint:

* the data settles ``setup time + setup slack`` before the edge
* the data changes again ``hold time + hold slack`` after the edge

The data changes within a window, from the hold capture edge to the setup capture edge, less the spread of the input or output delays:

.. code-block:: text

   window = (setup requirement - hold requirement) - (maximum delay - minimum delay)

The minimum delay is signed: a negative minimum, the usual case, narrows the window.
What the slacks leave of the window is how long the data takes to change, which sets the width of each row's ``X``.

The example eyes are beside their interface files, such as ``example/microchip/vsc8540et/mii_eye.txt``.
