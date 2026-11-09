RMII
====

RMII connects an Ethernet MAC to a PHY with two data bits each way and one 50 MHz reference clock, REF_CLK, which both ends receive.
Every signal is launched and captured on the rising edge of REF_CLK, so each is system synchronous: the clock reaches the two ends on separate traces from one source.
This page shows how stacv times RMII when the device is the MAC, through the steps of the :doc:`process`.

The signals
-----------

The signal names are the RMII specification's, revision 1.2 (see :doc:`standards`).

=========  ===================  ================  ====================================================================
Signal     Direction            Methodology       Notes
=========  ===================  ================  ====================================================================
REF_CLK    from a source        clock             From the PHY, the MAC or an oscillator, on a trace to each end.
TXD[1:0]   MAC to PHY           SDR-SYS-O
TX_EN      MAC to PHY           SDR-SYS-O
TX_ER      MAC to PHY           SDR-SYS-O         Optional.
RXD[1:0]   PHY to MAC           SDR-SYS-I
CRS_DV     PHY to MAC           SDR-SYS-I
RX_ER      PHY to MAC           SDR-SYS-I         Optional.
=========  ===================  ================  ====================================================================

The steps
---------

#. **Gather Inputs.**  The MAC's HDL, the PHY's datasheet, with its RMII setup, hold and output delay, and the delay of each trace, with REF_CLK's from its source to each end.

#. **Create Templates.**

   .. code-block:: text

      stacv create template rmii --output rmii

#. **Create Input Files.**

   * In ``rmii_config.toml``, REF_CLK's clock name and port, and the port and register of each signal; remove ``[tx_er]`` or ``[rx_er]`` if the design does not use it (see :doc:`rmii_config`).
   * In ``part.toml``, each pin's timing from the datasheet.
   * In ``traces.toml``, the delay of each trace, with REF_CLK's from its source to each end.

#. **Validate Input Files.**  ``stacv visualize block_diagram rmii_config.toml`` shows the paths; RMII's edges are fixed.
#. **Generate Constraints.**  ``stacv generate xdc`` and ``stacv generate report_tcl``, from the folder of ``rmii_config.toml``.
#. **Generate Timing Reports.**  Read the constraints into the design after synthesis, and source the report script after routing.
#. **Validate Timing Reports.**  ``stacv check rmii_config.toml``.

The VSC8540ET example in ``example/microchip/vsc8540et`` has an RMII interface timed this way, ``rmii_config.toml``, beside the hand-written interface file it reproduces, ``rmii.toml``.

Not supported yet
-----------------

* The device as the PHY.
