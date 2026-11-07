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
CS      device to part       SDR-SS-O-FLC      Timed to the first and last edges of SCK, which stops between transfers.
CIPO    part to device       SDR-SS-RT-DI      The part launches on the SCK it receives; the device captures with its own clock, so the timing makes a round trip.
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

   The launch and capture edges are worked out from the mode and the periods (see :doc:`create`).

#. Fill in the part's setup, hold, clock to out and fastest SCK from its datasheet, in ``part.toml``, or point ``part`` at a part file from a library that gives the SPI signals.
   stacv stops on each value still ``FROM_DATASHEET`` (part_config_011).
#. Fill in the trace delays from the board, in ``traces.toml``, or leave ``{}`` to use the default delay.
#. Rename the ports, clocks and registers to your design's, and ``SPI_INTERFACE_NAME`` everywhere it appears.
   Keep each ``if_signal``: it links the files.
#. Check the edges against the part's datasheet:

   .. code-block:: text

      stacv visualize edges interface.toml

#. Generate the constraints and the report script, apply the constraints, and run the report script in Vivado (see :doc:`generate`).
#. Check the timing reports, and look at the eye of each signal (see :doc:`eye`):

   .. code-block:: text

      stacv check interface.toml
      stacv visualize eye interface.toml

#. Move a capture edge to centre an eye, if the slacks are uneven, and go round again.
#. Generate the datasheet of the interface, for whoever connects a part to the device (see :doc:`datasheet`).

The DAC81404 example in ``example/texas_instruments/DAC81404`` is an SPI mode 1 interface timed this way, with a slower SCK for reads.

Not supported yet
-----------------

* The device as the peripheral.
* 3-wire SPI, with one data line, SDIO, in both directions.
