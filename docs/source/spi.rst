SPI
===

An SPI interface is not one timing problem but three: the data the device sends, the chip select, and the data it receives.
Each is a different :doc:`methodology <methodology>`, and SCK, the clock the device generates and sends to the part, ties them together.
This page shows how stacv times each signal when the device is the controller, through the steps of the :doc:`process`.

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

The modes
---------

The mode, ``--mode`` and ``mode``, is the standard SPI mode, 0 to 3, set by the clock's polarity (CPOL) and phase (CPHA).
The part's datasheet gives it, or the edges it samples and changes data on.

==========  ====  ====  ==========  ===================  ===================
Mode        CPOL  CPHA  SCK idles   Data changes on      Data sampled on
==========  ====  ====  ==========  ===================  ===================
0           0     0     low         falling edge         rising edge
1           0     1     low         rising edge          falling edge
2           1     0     high        rising edge          falling edge
3           1     1     high        falling edge         rising edge
==========  ====  ====  ==========  ===================  ===================

So, in every mode:

* COPI changes on the change edge and the part samples it on the next sample edge.
* CS is asserted before the first sample edge of a transfer and deasserted after the last.
* CIPO changes on the change edge, and the device captures it with its own clock, at about the time of the next sample edge.

The steps
---------

#. **Gather Inputs.**  The HDL of the SPI controller, the part's datasheet, with its SPI mode and its setup, hold and clock to out, and the delay of each trace.

#. **Create Templates.**  Create the three files for the mode, with the device clock's and SCK's periods:

   .. code-block:: text

      stacv create template spi --wires 4 --mode 0 --type controller --clock-period 10 --sck-period 80 --output spi

   They are the SPI configuration, ``spi_config.toml``, the part file and the traces file (see :doc:`create`).

#. **Create Input Files.**

   * In ``spi_config.toml``, the device clock, and the port and register of each signal, from the HDL; stacv stops on each still ``FROM_DESIGN_...``.
     Each launch and capture is counted in device clocks from a named edge of SCK, such as ``assert = {sck_edge = "first sample", clocks = -4, source = "..."}``, with the line of the HDL it comes from.
     The template gives the usual edges for the mode; correct them from the HDL.
     A part that reads at a slower SCK than it is written at takes ``read_period`` (see :doc:`spi_config`).
   * In ``part.toml``, each pin's setup, hold, clock to out and fastest SCK, with its symbol and where it is in the datasheet; stacv stops on each still ``FROM_DATASHEET_...``.
     A part file from a library that gives the SPI signals can be named in place of one.
   * In ``traces.toml``, the delay of each trace, or ``{}`` for the default delay.

#. **Validate Input Files.**  Check the edges against the part's datasheet and the HDL, and the block diagram against the design:

   .. code-block:: text

      stacv visualize edges spi_config.toml
      stacv visualize block_diagram spi_config.toml

#. **Generate Constraints.**  Generate the constraints and the report script, from the folder of ``spi_config.toml``:

   .. code-block:: text

      stacv generate xdc spi_config.toml --output interface.xdc
      stacv generate report_tcl spi_config.toml --output report.tcl

#. **Generate Timing Reports.**  Read ``interface.xdc`` into the design after synthesis, implement it, and source ``report.tcl`` after routing, from the folder of ``spi_config.toml``.

#. **Validate Timing Reports.**

   .. code-block:: text

      stacv check spi_config.toml

Then, if CIPO's slacks are uneven, move its capture to centre its eye (see :doc:`eye`), and generate the interface's datasheet for whoever connects a part to the device next (see :doc:`datasheet`).

The DAC39RF20 example in ``example/texas_instruments/DAC39RF20`` is an SPI mode 0 interface timed this way, with its design and its timing reports.

Not supported yet
-----------------

* The device as the peripheral.
* 3-wire SPI, with one data line, SDIO, in both directions.
* A bus shared by several parts; each part is its own interface.
