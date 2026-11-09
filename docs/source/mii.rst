MII
===

MII connects an Ethernet MAC to a PHY with four data bits each way, and two clocks the PHY sends: TX_CLK for the data to the PHY, and RX_CLK for the data from it.
The MAC launches its data on the TX_CLK it receives, so the transmit data makes a round trip; the PHY sends the receive data with RX_CLK.
This page shows how stacv times MII when the device is the MAC, through the steps of the :doc:`process`.

The signals
-----------

The signal names are IEEE 802.3 Clause 22's (see :doc:`standards`).

=========  ===================  ================  ====================================================================
Signal     Direction            Methodology       Notes
=========  ===================  ================  ====================================================================
TX_CLK     PHY to MAC           clock             25 MHz at 100 Mbit/s, 2.5 MHz at 10 Mbit/s.
TXD[3:0]   MAC to PHY           SDR-SS-RT-DO      Launched on TX_CLK.
TX_EN      MAC to PHY           SDR-SS-RT-DO
TX_ER      MAC to PHY           SDR-SS-RT-DO      Optional.
RX_CLK     PHY to MAC           clock
RXD[3:0]   PHY to MAC           SDR-SS-I          Sent with RX_CLK.
RX_DV      PHY to MAC           SDR-SS-I
RX_ER      PHY to MAC           SDR-SS-I          Optional.
CRS, COL   PHY to MAC           not timed         Asynchronous.
=========  ===================  ================  ====================================================================

The steps
---------

#. **Gather Inputs.**  The MAC's HDL, the PHY's datasheet, with its MII setup, hold and output delay, and the delay of each trace.

#. **Create Templates.**

   .. code-block:: text

      stacv create template mii --output mii

#. **Create Input Files.**

   * In ``mii_config.toml``, each clock's name and port, and the port and register of each signal; remove ``[tx_er]`` or ``[rx_er]`` if the design does not use it (see :doc:`mii_config`).
   * In ``part.toml``, each pin's timing from the datasheet.
   * In ``traces.toml``, the delay of each trace, the clocks' included.

#. **Validate Input Files.**  ``stacv visualize block_diagram mii_config.toml`` shows the paths; MII's edges are fixed.
#. **Generate Constraints.**  ``stacv generate xdc`` and ``stacv generate report_tcl``, from the folder of ``mii_config.toml``.
#. **Generate Timing Reports.**  Read the constraints into the design after synthesis, and source the report script after routing.
#. **Validate Timing Reports.**  ``stacv check mii_config.toml``.

The VSC8540ET example in ``example/microchip/vsc8540et`` has an MII interface timed this way, ``mii_config.toml``, beside the hand-written interface file it reproduces, ``mii.toml``.

Not supported yet
-----------------

* The device as the PHY.
