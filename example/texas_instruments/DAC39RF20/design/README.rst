DAC39RF20 start-up design
=========================

A small FPGA design that brings up a Texas Instruments DAC39RF20 over its standard SPI interface
(datasheet SBASAO8A), for timing with stacv.

* Target: xc7a12tcpg238-2, 100 MHz board clock on ``clk_100m``.
* SPI mode 0 at 12.5 MHz (100 MHz / 8; the DAC allows 15 MHz), 1.8 V I/O in bank 34.
* After reset it holds ``dac_resetn`` low for 160 ns, waits 10 us, writes DEVICE_CONFIG,
  then reads CHIP_TYPE, CHIP_ID and VENDOR_ID and lights ``led_id_ok`` when they match.

=====================  ===========================================================
File                   Contents
=====================  ===========================================================
hdl/spi_master.vhd     SPI controller: 24-bit accesses, every pin from or to a register
hdl/dac39rf20_init.vhd Start-up sequencer
hdl/dac39rf20_top.vhd  Top level
constraints/           Board constraints: system clock and pins.  No SPI timing.
sim/                   Testbench with a model of the DAC39RF20 SPI port
design.tcl             Top, part and sources, for ``bin/vivado_loop``
=====================  ===========================================================

The SPI interface constraints are left for the interface constraints file.

Build and check
---------------

From the repository root, with Vivado on the PATH (or ``VIVADO_SETTINGS`` naming its ``settings64.sh``)::

   bin/vivado_loop example/texas_instruments/DAC39RF20/design/design.tcl \
       --xdc <interface constraints> --report-tcl <report script> --interface <interface.toml>

Without the options it only builds the design.  The build goes to ``design/build/``.

With ``--interface``, the report script runs in the interface file's folder, so its relative
``timing_reports`` paths mean the same to Vivado as to ``stacv check``: generate the report script
from that folder.  The report folders are created before Vivado runs.

Simulate
--------

::

   xvhdl --2008 hdl/*.vhd sim/*.vhd
   xelab dac39rf20_top_tb -s tb
   xsim tb -R
