Commands
========

Each step of the :doc:`process` is a stacv command: a verb, then what it acts on.
Every command that reads an interface takes either an interface file or an interface configuration file, such as ``spi_config.toml``.

Run ``stacv`` alone to list the commands.
A command given without its arguments, or with a wrong one, prints its help and then the error, so each next word can be found from the terminal.
An input error is one line on standard error, and stacv exits with code 2 (see :doc:`errors`).

stacv create
------------

Writes templates to fill in: an interface, part or traces file, or the three files of an SPI interface for its mode, role and clock periods.
An existing file is never overwritten.

.. code-block:: text

   stacv create template spi --wires 4 --mode 0 --type controller --clock-period 10 --sck-period 80 --output dac_spi
   stacv create template part --output part.toml

See :doc:`create`.

stacv visualize
---------------

Draws what the input files say, to compare with the design and the datasheet before the timing tool runs, and the eye of each port once it has.

.. code-block:: text

   stacv visualize edges spi_config.toml
   stacv visualize block_diagram spi_config.toml
   stacv visualize eye spi_config.toml

* ``edges``: each port's launch and capture edges, numbered on each clock from 0, and its setup and hold requirements.
  It reads only the interface file, so it can be run before the part and traces files are filled in.
* ``block_diagram``: the registers, clocks, ports, traces and part pins of each path (see :doc:`block_diagram`).
* ``eye``: where each port's data sits in its window, with its setup and hold slack in each corner, from the timing reports (see :doc:`eye`).

stacv generate
--------------

Writes the files the timing tool reads, and the interface's datasheet.
Each is written to standard output, or to the file ``--output`` names.

.. code-block:: text

   stacv generate xdc spi_config.toml --output interface.xdc
   stacv generate report_tcl spi_config.toml --output report.tcl
   stacv generate interface spi_config.toml --output interface.toml
   stacv generate datasheet spi_config.toml --output datasheet.toml

* ``xdc``: the constraints, each explained (see :doc:`generate`).
* ``report_tcl``: the script that writes a timing report for each port; source it in the timing tool after routing, from the folder of the interface file.
* ``interface``: the interface file an interface configuration file expands to (see :doc:`spi_config`).
* ``datasheet``: the interface's timing at the device's pins, from the timing reports (see :doc:`datasheet`).

stacv check
-----------

Checks the timing reports against the input files, and prints PASSED or FAILED for each port.

.. code-block:: text

   stacv check spi_config.toml
   stacv check spi_config.toml --report check_report.txt --junit check.xml

It exits with code 0 when every port passes, 1 when a rule fails, and 2 on an input error.
``--report`` writes a report file with a summary, the md5sum of every input, and each rule's result; ``--junit`` writes a JUnit file for a CI system (see :doc:`check_output`).
