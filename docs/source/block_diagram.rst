Block Diagram
=============

``stacv visualize block_diagram`` draws the device, the part and the traces between them, with the registers that drive and capture each port and the clocks of those registers.
It shows exactly what is timed: each path runs from a register, through a port and a trace, to a pin of the part, or back.
The same drawing is section 2 of the constraints file ``stacv generate xdc`` writes.

.. code-block:: text

   stacv visualize block_diagram interface.toml

It reads the interface, traces and part files, so it is drawn before timing, and checks them as ``stacv check`` does.

Reading the diagram
-------------------

The DAC81404 example:

.. code-block:: text

   ---------------------------------------------------------------+                       +------------
     Device                                                       |                       |  DAC81404
                                                                  |                       |
     clk_100mhz --+--> [q_spi_output_data_reg] ---> O_DAC_DATA   [X] --- data_output --> [X] SDIN
                  |                                               |                       |
                  +--> [q_spi_sden_f_reg] --------> O_DAC_SDEN_F [X] --- chip_select --> [X] CSF
                  |                                               |                       |
                  +--> [q_spi_input_data_reg] <---- I_DAC_DATA   [X] <-- data_input ---- [X] SDO
                  |                                               |                       |
                  +--> [q_spi_output_clock_reg] --> O_DAC_SCLK   [X] --- clock --------> [X] SCLK
                                                                  |                       |
   ---------------------------------------------------------------+                       +------------

* The device is on the left and the part on the right; each ``[X]`` on an edge is a port of the device or a pin of the part, and the trace between them is named on its arrow.
* Each clock that clocks a register roots a tree, ``clk_100mhz --+``, and each register hangs from it, ``+--> [q_spi_output_data_reg]``.
  The clock is the launch clock of an output, the capture clock of an input, and the master clock of a clock the device generates, such as O_DAC_SCLK.
* The arrow between a register and its port points the way the data goes: ``--->`` from a register that drives the port, ``<----`` to a register that captures it.
* Each register is drawn as written in the interface file, wildcards included.

A port with several registers joins them before the port.
Only a register's own end has an arrow; the join meets the port with ``-->`` when any register drives it.
The VSC8540ET's MDIO is driven by two registers and captured by a third:

.. code-block:: text

   ------------------------------------------------------+                +-------------
     Device                                              |                |  VSC8540ET
                                                         |                |
     clk_100mhz --+--> [q_mdio_out_reg] --+--> IO_MDIO  [X] <-- mdio --> [X] MDIO
                  |                       |              |                |
                  +--> [q_mdio_oe_reg] ---+              |                |
                  |                       |              |                |
                  +--> [q_mdio_in_reg] <--+              |                |
                  |                                      |                |
                  +--> [q_mdc_reg] -----------> O_MDC   [X] --- mdc ---> [X] MDC
                                                         |                |
   ------------------------------------------------------+                +-------------

A clock that enters the device on a port roots its tree on that port's row: the clock comes out of the port, to the left, and its registers hang below.
The VSC8540ET's MII clocks both come from the PHY:

.. code-block:: text

   -----------------------------------------------------------+                      +-------------
     Device                                                   |                      |  VSC8540ET
                                                              |                      |
     mii_tx_clk <-+-------------------------- I_MII_TX_CLK   [X] <-- mii_tx_clk --- [X] MII_TXCLK
                  |                                           |                      |
                  +--> [q_mii_txd_reg[*]] --> O_MII_TXD[3:0] [X] --- mii_txd -----> [X] TXD[3:0]
                  |                                           |                      |
                  +--> [q_mii_tx_en_reg] ---> O_MII_TX_EN    [X] --- mii_tx_en ---> [X] TX_EN
                  |                                           |                      |
                  +--> [q_mii_tx_er_reg] ---> O_MII_TX_ER    [X] --- mii_tx_er ---> [X] TX_ER
                                                              |                      |
     mii_rx_clk <-+-------------------------- I_MII_RX_CLK   [X] <-- mii_rx_clk --- [X] RX_CLK
                  |                                           |                      |
                  +--> [q_mii_rxd_reg[*]] <-- I_MII_RXD[3:0] [X] <-- mii_rxd ------ [X] RXD[3:0]
                  |                                           |                      |
                  +--> [q_mii_rx_dv_reg] <--- I_MII_RX_DV    [X] <-- mii_rx_dv ---- [X] RX_DV
                  |                                           |                      |
                  +--> [q_mii_rx_er_reg] <--- I_MII_RX_ER    [X] <-- mii_rx_er ---- [X] RX_ER
                                                              |                      |
   -----------------------------------------------------------+                      +-------------

A clock from a source, outside both the device and the part, comes in from the top edge, between the boxes, to a ``+`` that sends it to both.
Its trees are drawn first, so the source never crosses another trace.
The VSC8540ET's RMII reference clock:

.. code-block:: text

   ---------------------------------------------------------------+                    (phy_rmii_clkout)                  +---------------------
     Device                                                       |                            v                          |  VSC8540ET
                                                                  |                            |                          |
     rmii_ref_clk <-+--------------------------- I_RMII_REF_CLK  [X] <-- rmii_clk_to_device ---+--- rmii_clk_to_part --> [X] RMII_CLKIN
                    |                                             |                                                       |
                    +--> [q_rmii_txd_reg[*]] --> O_RMII_TXD[1:0] [X] --- rmii_txd -------------------------------------> [X] TXD[1:0]
                    |                                             |                                                       |
                    +--> [q_rmii_tx_en_reg] ---> O_RMII_TX_EN    [X] --- rmii_tx_en -----------------------------------> [X] TX_EN
                    |                                             |                                                       |
                    +--> [q_rmii_tx_er_reg] ---> O_RMII_TX_ER    [X] --- rmii_tx_er -----------------------------------> [X] TX_ER
                    |                                             |                                                       |
                    +--> [q_rmii_rxd_reg[*]] <-- I_RMII_RXD[1:0] [X] <-- rmii_rxd -------------------------------------- [X] RXD[1:0]
                    |                                             |                                                       |
                    +--> [q_rmii_crs_dv_reg] <-- I_RMII_CRS_DV   [X] <-- rmii_crs_dv ----------------------------------- [X] CRS_DV
                    |                                             |                                                       |
                    +--> [q_rmii_rx_er_reg] <--- I_RMII_RX_ER    [X] <-- rmii_rx_er ------------------------------------ [X] RX_ER
                                                                  |                                                       |
   ---------------------------------------------------------------+                                                       +---------------------

A port with no registers, such as a deferred port, is drawn on its own after the trees, and so is a clock the device forwards without a ``generator``.
