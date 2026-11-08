SPI Configuration File
======================

The SPI configuration file holds what only the user knows about an SPI interface: the names in the design, the SPI mode, and where the part and trace files are.
Everything the mode already fixes, the methodology of each signal, its interface signal and its edges, stacv works out.

It is the source of the interface:

* The user edits three files: the SPI configuration, the part file (see :doc:`part`) and the traces file (see :doc:`traces`).
* Every command reads the SPI configuration in place of an interface file, and expands it into the interface file it times (see :doc:`interface`) whenever it runs.
  The interface file is never written unless it is asked for, so it cannot fall out of step with the configuration.
* An interface stacv has no configuration for yet is timed with an interface file written by hand.

``stacv create template spi`` creates the three files (see :doc:`create`).

An example
----------

The SPI configuration of the DAC39RF20 start-up design in ``example/texas_instruments/DAC39RF20``:

.. literalinclude:: ../../example/texas_instruments/DAC39RF20/spi_config.toml
   :language: toml

Keys
----

Top level
^^^^^^^^^

======================  ==========================================================================================
Key                     Value
======================  ==========================================================================================
``interface``           ``"spi"``.  It marks the file as an interface configuration file.
``name``                The name of the interface.  It names the timing reports, and the constraints file's header.
``mode``                The SPI mode, ``0`` to ``3`` (see :doc:`standards`).
``role``                The device's role, ``"controller"``.  A peripheral is not supported yet.
``part``                The part file, a path relative to this file.  A library of parts is a folder of part files.
``traces``              The traces file, a path relative to this file.
``timing_reports_dir``  The folder the timing reports are written to and read from, relative to this file.
======================  ==========================================================================================

Paths can start with an environment variable, such as ``$PROJ_DIR/build/timing_reports``.

Tables
^^^^^^

==================  ==================================  ================================================================
Table               Keys                                Value
==================  ==================================  ================================================================
``[device_clock]``  ``name``, ``period``                The device clock the SPI logic runs on, as the constraints name it, and its period in ns.
``[sck]``           ``port``, ``register``, ``period``  The port SCK leaves the device on, the register that generates it, and its period in ns, an even number of device clock periods.
                    ``read_period``                     Optional: the period of a slower SCK for reads, when the part's CIPO allows a lower SCK frequency than its inputs.
``[copi]``          ``port``, ``register``, ``launch``  The port COPI, the data from the device into the part, leaves on, the register that drives it, and when it launches.
``[cipo]``          ``port``, ``register``,             The port CIPO, the data from the part into the device, arrives on, the register that captures it, and when.
                    ``capture``
``[cs]``            ``port``, ``register``,             The port CS leaves on, the register that drives it, and when it is asserted and deasserted.
                    ``assert``, ``deassert``
==================  ==================================  ================================================================

Registers are named as Vivado names them: the hierarchy separated by ``/``, with ``_reg`` added, and a bit of a bus in brackets, such as ``u_spi/rx_shift_reg[0]``.
A name still ``FROM_DESIGN``, as the template writes it, stops every command (spi_config_006).

Edges
-----

Each edge says when the design launches or captures a signal, the way the HDL counts it: a number of device clocks from a named edge of SCK, and where in the design it comes from.

.. code-block:: toml

   launch   = {sck_edge = "change", clocks = 0, source = "spi_master.vhd: SCLK_HIGH sets sdi_q with sclk_q low"}

* ``sck_edge`` names the edge of SCK it is counted from.
  The mode sets which SCK edges are change edges and which are sample edges.
* ``clocks`` counts device clock periods from that edge: ``-4`` is four periods before it, ``0`` the device clock edge that makes the SCK edge, ``0.5`` half a period after it, for a register on the falling edge of the device clock.
  It is a whole or half number (spi_config_015).
* ``source`` says where in the design the edge comes from.
  It is required, and ``FROM_DESIGN``, as the template writes it, stops every command (spi_config_006), as the edges are the judgement in the file.

============  =================================  ===========================================================  ====================================================
Key           ``sck_edge``                       Counted from                                                 Must stay
============  =================================  ===========================================================  ====================================================
``launch``    ``"change"``                       The SCK change edge before the sample edge that captures     At or after the sample edge of the bit before it,
of [copi]                                        the bit                                                      and before the sample edge that captures it
``capture``   ``"sample"``                       The SCK sample edge after the change edge the part           The hold capture at or after edge 0 and at or before
of [cipo]                                        launches the bit on                                          the launching edge, the setup capture after it
``assert``    ``"first sample"``                 The first SCK sample edge of the transfer                    At or after edge 0, and before the first sample edge
of [cs]
``deassert``  ``"last change"`` or               The last SCK change edge, or the last sample edge, of the    At or after the last sample edge.  SCK has stopped,
of [cs]       ``"last sample"``                  transfer                                                     so there is no later limit.
============  =================================  ===========================================================  ====================================================

The template writes the usual values for the mode: COPI launched and CIPO captured at their SCK edges, CS asserted one SCK period before the first sample edge and deasserted at the last change edge.
Read the HDL, correct them, and check them with ``stacv visualize edges spi_config.toml``.
An edge outside its range stops every command (spi_config_011), and an ``sck_edge`` the key is not counted from is spi_config_014.

Until the design is simulated against them, the edges are the ones the configuration gives.
The constraints file lists each one with its source, in its references:

.. code-block:: text

   # Edges:      set in the SPI configuration, not verified against simulation
   #             COPI launch   at the SCK change edge                     spi_master.vhd: SCLK_HIGH sets sdi_q with sclk_q low
   #             CIPO capture  at the SCK sample edge                     spi_master.vhd: SCLK_LOW shifts sdo into rx_shift with sclk_q high
   #             CS assert     4 clocks before the first SCK sample edge  spi_master.vhd: IDLE clears scs_n_q with the first bit, HALF_PERIOD before sclk_q rises
   #             CS deassert   4 clocks after the last SCK change edge    spi_master.vhd: TRAIL sets scs_n_q HALF_PERIOD after the last sclk_q fall

The interface it expands to
---------------------------

* SCK is a clock named after its port with ``_clk``, such as ``dac_sclk_clk``, generated by its register from the device clock.
* With ``read_period``, a second clock on the same port, named with ``_rd_clk``, has the read period, and CIPO is timed on it: the part launches CIPO on the read SCK, and the device captures it counted from the read SCK's sample edge.
* Each timing report is named by the interface and the signal, in the reports folder: ``<timing_reports_dir>/<name>.<signal>_timing.rpt``, such as ``design/build/timing_reports/DAC_SPI.COPI_timing.rpt``.
* The part's interface is the one that follows the mode, as the peripheral: its ``if_standard`` is ``SPI mode <mode>`` and its ``if_role`` is ``peripheral``.
  A part with none, or with more than one, stops every command once the part file exists (spi_config_012, spi_config_013).

``stacv generate interface`` writes the interface file, to read it or to take it over when a design needs what the configuration cannot give:

.. code-block:: text

   stacv generate interface spi_config.toml --output interface.toml

Its paths are relative to the folder of the SPI configuration, so write it to the same folder.

Not supported yet
-----------------

* The device as the peripheral.
* 3-wire SPI.
* A bus shared by several parts.
  Each part is its own interface, with its own SPI configuration.
