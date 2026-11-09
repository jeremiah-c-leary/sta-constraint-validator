RMII Configuration File
=======================

The RMII configuration file holds what only the user knows about an RMII interface with the device as the MAC: the names in the design, and where the part and trace files are.
RMII fixes everything else: REF_CLK runs at 50 MHz, and every signal is launched and captured on its rising edge, at both ends.
Every command reads it in place of an interface file, and expands it into the interface file it times; ``stacv generate interface`` writes that file.

``stacv create template rmii`` creates it, with the part and traces files (see :doc:`create`).

An example
----------

The VSC8540ET example's RMII interface, in ``example/microchip/vsc8540et``:

.. literalinclude:: ../../example/microchip/vsc8540et/rmii_config.toml
   :language: toml

Keys
----

==========================  ==========================================================================================
Key                         Value
==========================  ==========================================================================================
``interface``               ``"rmii"``.  It marks the file as an RMII configuration file.
``name``                    The name of the interface.  It names the timing reports.
``role``                    The device's role, ``"MAC"``.  A PHY is not supported yet.
``part``                    The part file, a path relative to this file.
``traces``                  The traces file, a path relative to this file.
``timing_reports_dir``      The folder the timing reports are written to and read from, relative to this file.
``[ref_clk]``               ``name``: the name stacv creates the clock with; ``port``: the port REF_CLK arrives on.
``[txd]``, ``[tx_en]``      ``port`` and ``register`` of each signal from the MAC to the PHY.
``[tx_er]``                 The same, and optional: remove it, and its trace, if the design does not use TX_ER.
``[rxd]``, ``[crs_dv]``     ``port`` and ``register`` of each signal from the PHY to the MAC.
``[rx_er]``                 The same, and optional.
==========================  ==========================================================================================

A value still ``FROM_DESIGN_...``, as the template writes it, stops every command (rmii_config_006).
A bus port is written ``NAME[upper:lower]``, such as ``O_RMII_TXD[1:0]``, and its register ``reg[*]`` (rmii_config_014).
stacv creates REF_CLK's clock on its port; if the board constraints already create one there, Vivado warns of the two, so remove the other.

The interface it expands to
---------------------------

* REF_CLK is created on its port with a period of 20 ns.
* TXD, TX_EN and TX_ER are timed as SDR-SYS-O, and RXD, CRS_DV and RX_ER as SDR-SYS-I: launched on a rising edge of REF_CLK and captured on the next.
  Where REF_CLK comes from, the PHY, the MAC or an oscillator, is in the traces file, as its delay to each end.
* Each timing report is named by the interface and the signal: ``<timing_reports_dir>/<name>.<signal>_timing.rpt``.
* The part's interface is the one that follows RMII as the PHY (rmii_config_012, rmii_config_013).
* A part pin of an optional signal the interface leaves out needs no port.
