MII Configuration File
======================

The MII configuration file holds what only the user knows about an MII interface with the device as the MAC: the names in the design, and where the part and trace files are.
MII fixes everything else: the PHY sends TX_CLK and RX_CLK, and every signal is launched on a rising edge of its clock and captured on the next.
Every command reads it in place of an interface file, and expands it into the interface file it times; ``stacv generate interface`` writes that file.

``stacv create template mii`` creates it, with the part and traces files (see :doc:`create`).

An example
----------

The VSC8540ET example's MII interface, in ``example/microchip/vsc8540et``:

.. literalinclude:: ../../example/microchip/vsc8540et/mii_config.toml
   :language: toml

Keys
----

==========================  ==========================================================================================
Key                         Value
==========================  ==========================================================================================
``interface``               ``"mii"``.  It marks the file as an MII configuration file.
``name``                    The name of the interface.  It names the timing reports.
``role``                    The device's role, ``"MAC"``.  A PHY is not supported yet.
``part``                    The part file, a path relative to this file.
``traces``                  The traces file, a path relative to this file.
``timing_reports_dir``      The folder the timing reports are written to and read from, relative to this file.
``[tx_clk]``, ``[rx_clk]``  ``name``: the name stacv creates the clock with; ``port``: the port the clock arrives on.
``[txd]``, ``[tx_en]``      ``port`` and ``register`` of each signal from the MAC to the PHY.
``[tx_er]``                 The same, and optional: remove it, and its trace, if the design does not use TX_ER.
``[rxd]``, ``[rx_dv]``      ``port`` and ``register`` of each signal from the PHY to the MAC.
``[rx_er]``                 The same, and optional.
==========================  ==========================================================================================

A value still ``FROM_DESIGN_...``, as the template writes it, stops every command (mii_config_006).
A bus port is written ``NAME[upper:lower]``, such as ``O_MII_TXD[3:0]``, and its register ``reg[*]`` (mii_config_014).
stacv creates each clock on its port; if the board constraints already create one there, Vivado warns of the two, so remove the other.

The interface it expands to
---------------------------

* TX_CLK and RX_CLK are created on their ports with a period of 40 ns, 25 MHz at 100 Mbit/s.
  At 10 Mbit/s the clocks are 2.5 MHz with the same timing at the pins, so timing at 25 MHz covers both.
* TXD, TX_EN and TX_ER are timed as SDR-SS-RT-DO: launched on a rising edge of the TX_CLK the MAC receives, and captured by the PHY on the next.
* RXD, RX_DV and RX_ER are timed as SDR-SS-I: sent with RX_CLK on a rising edge, and captured by the MAC on the next.
* CRS and COL are asynchronous, so they are not timed.
* Each timing report is named by the interface and the signal: ``<timing_reports_dir>/<name>.<signal>_timing.rpt``.
* The part's interface is the one that follows MII as the PHY (mii_config_012, mii_config_013).
* A part pin of an optional signal the interface leaves out needs no port.
