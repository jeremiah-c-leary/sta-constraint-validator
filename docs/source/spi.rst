Timing an SPI Interface
=======================

An SPI interface is not one timing problem but three: the data the device sends, the chip select, and the data it receives.
Each is a different :doc:`methodology <methodology>`, and SCK, the clock the device generates and sends to the part, ties them together.
This page shows how stacv times each signal, when the device is the controller.

The signals
-----------

The signal names are the Open Source Hardware Association's (see :doc:`standards`).

======  ===================  ================  ====================================================================
Signal  Direction            Methodology       Why
======  ===================  ================  ====================================================================
SCK     device to part       generated clock   The device divides it from its own clock and forwards it with the data.
COPI    device to part       SDR-SS-O          The device sends data and the clock that captures it, together (see :doc:`methodology/sdr_ss_o`).
CS      device to part       SDR-SS-O-FLC      Timed to the first and last edges of SCK, which stops between transfers (see :doc:`methodology/sdr_ss_o_flc`).
CIPO    part to device       SDR-SS-RT-DI      The part launches on the SCK it receives; the device captures with its own clock, so the timing makes a round trip (see :doc:`methodology/sdr_ss_rt_di`).
======  ===================  ================  ====================================================================

The mode sets which SCK edge data changes on and which it is sampled on:

* COPI changes on the change edge and the part samples it on the next sample edge.
* CS is set before the first sample edge of a transfer and cleared after the last.
* CIPO changes on the change edge; the device captures it with its own clock, at the time of the next sample edge.

The steps
---------

#. Create the three files for the mode, with the device clock's and SCK's periods:

   .. code-block:: text

      stacv create template spi --wires 4 --mode 1 --type controller --clock-period 10 --sck-period 40 --output spi

   They are the SPI configuration, ``spi_config.toml``, the part file and the traces file.
   The launch and capture edges are worked out from the mode and the periods (see :doc:`create` and :doc:`spi_config`).

#. Fill in the part's setup, hold, clock to out and fastest SCK from its datasheet, in ``part.toml``, or point ``part`` at a part file from a library that gives the SPI signals.
   stacv stops on each value still ``FROM_DATASHEET`` (part_config_011).
#. Fill in the trace delays from the board, in ``traces.toml``, or leave ``{}`` to use the default delay.
#. Fill in the names in your design, the device clock, and the port and register of each signal, in ``spi_config.toml``.
   stacv stops on each name still ``FROM_DESIGN`` (spi_config_006).
#. Set when the design launches and captures each signal, in device clocks from an edge of SCK, with the line of the HDL it comes from, and check the edges against the part's datasheet:

   .. code-block:: text

      stacv visualize edges spi_config.toml

#. Generate the constraints and the report script, apply the constraints, and run the report script in Vivado (see :doc:`generate`).
#. Check the timing reports, and look at the eye of each signal (see :doc:`eye`):

   .. code-block:: text

      stacv check spi_config.toml
      stacv visualize eye spi_config.toml

#. Move CIPO's capture to centre its eye, if the slacks are uneven, and go round again.
#. Generate the datasheet of the interface, for whoever connects a part to the device (see :doc:`datasheet`).

The DAC39RF20 example in ``example/texas_instruments/DAC39RF20`` is an SPI mode 0 interface timed this way.
The DAC81404 example in ``example/texas_instruments/DAC81404`` is an SPI mode 1 interface with a slower SCK for reads, timed with a hand-written interface file; an SPI configuration gives the same interface with ``read_period``.

Not supported yet
-----------------

* The device as the peripheral.
* 3-wire SPI, with one data line, SDIO, in both directions.
* A bus shared by several parts; each part is its own interface.
