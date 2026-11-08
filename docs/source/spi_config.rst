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
``[copi]``          ``port``, ``register``, ``adjust``  The port COPI, the data from the device into the part, leaves on, and the register that drives it.
``[cipo]``          ``port``, ``register``, ``adjust``  The port CIPO, the data from the part into the device, arrives on, and the register that captures it.
``[cs]``            ``port``, ``register``,             The port CS leaves on, and the register that drives it.
                    ``setup_adjust``, ``hold_adjust``
==================  ==================================  ================================================================

Registers are named as Vivado names them: the hierarchy separated by ``/``, with ``_reg`` added, and a bit of a bus in brackets, such as ``u_spi/rx_shift_reg[0]``.
A name still ``FROM_DESIGN``, as the template writes it, stops every command (spi_config_006).

Edges
-----

Each signal is launched and captured on the edges the mode defines, numbered on the device clock from SCK's edge A:

* COPI is launched on the change edge before the first sample edge, and captured on the sample edges either side of it.
* CS is set one SCK period before the first sample edge, and cleared at the change edge after the last.
* CIPO is launched by the part on SCK's change edge, and captured by the device at the sample edges either side of it.

When the design launches a signal on another device clock edge, the adjust keys move it.
An adjust is a whole number of device clock edges: ``+1`` is one edge later, ``-1`` one edge earlier, so ``+2`` is one device clock period.
An odd adjust moves a launch to a falling edge of the device clock, for a design that launches on it.

=================  ====================================  ==============================================================
Key                Moves                                 Must stay
=================  ====================================  ==============================================================
``adjust`` of      The launch of COPI                    At or after the sample edge of the bit before it, and before
``[copi]``                                               the sample edge that samples it.
``setup_adjust``   The launch that sets CS               At or after edge 0, and before the first sample edge.
``hold_adjust``    The launch that clears CS             At or after the last sample edge.  SCK has stopped, so there
                                                         is no later limit.
``adjust`` of      Both captures of CIPO by the device   The hold capture at or after edge A, and at or before the edge
``[cipo]``                                               that launches CIPO, and the setup capture after it.
=================  ====================================  ==============================================================

An adjust left out is ``0``.
An adjust that moves an edge outside its range stops every command (spi_config_011).
Check the edges with ``stacv visualize edges spi_config.toml``.

Until the design is simulated against them, the edges are the mode's, moved by the adjusts the user gave.
The constraints file says so in its references, such as::

   # Edges:      SPI mode 0 defaults; CS setup +8, hold +8; not verified against simulation

The interface it expands to
---------------------------

* SCK is a clock named after its port with ``_clk``, such as ``dac_sclk_clk``, generated by its register from the device clock.
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
