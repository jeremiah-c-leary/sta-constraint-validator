Creating Templates
==================

stacv creates a template of each file an interface needs, to start a new interface from.

.. code-block:: text

   stacv create template interface --output interface.toml
   stacv create template traces --output traces.toml
   stacv create template part --output part.toml

Each template is written to standard output, or to the file named by ``--output``.

The templates are complete files with placeholder values, such as ``INTERFACE_NAME`` and ``PART_NUMBER``.
Each starts with a link to the page describing its keys: :doc:`interface`, :doc:`traces` and :doc:`part`.

The three templates describe the same interface, so they can be used together before any value is filled in.
Created in one directory with the names above, they are read by ``stacv visualize`` and ``stacv generate``:

.. code-block:: text

   stacv visualize block_diagram interface.toml

The templates show:

* An interface with a launch clock and a generated capture clock that leaves the device on a clock port.
* One analyzed SDR-SS-O output port, one deferred output port, and one deferred input port.
* A trace for each port and for the clock, including a trace that uses the default delay.
* Part pins with SDR-SS-I and SDR-SS-RT-DO timing, one for each data and chip select trace.

Copy a table to add more clocks, ports, traces or pins.

SPI
---

``stacv create template spi`` creates the three files of an SPI interface: its SPI configuration, its part file and its traces file (see :doc:`spi_config`, :doc:`standards` and :doc:`spi`):

.. code-block:: text

   stacv create template spi --wires 4 --mode 1 --type controller --clock-period 10 --sck-period 40 --output spi

==================  =========================================================================================
Option              Description
==================  =========================================================================================
``--wires``         Required: the number of wires, ``4``.  ``3`` is not supported yet (create_004).
``--mode``          Required: the SPI mode, ``0`` to ``3``.
``--type``          Required: the device's role, ``controller``.  ``peripheral`` is not supported yet (create_004).
``--clock-period``  The period of the device clock that generates SCK, in ns; 10 without it.
``--sck-period``    The period of SCK, in ns, an even number of device clock periods (create_005); 40 without it.
``--output``        The directory the three files are written to, the current directory without it.
==================  =========================================================================================

``spi_config.toml``, ``part.toml`` and ``traces.toml`` are written to the directory, which is created when it does not exist.
The command each was created by is at its top.

* ``spi_config.toml`` holds the mode, the role and the periods from the command line, and ``FROM_DESIGN`` for each name in the design, which stacv stops on until it is filled in (spi_config_006).
  The interface file is not written: stacv expands the SPI configuration into it whenever a command runs.
* Each launch and capture is written with the usual value for the mode, in device clocks from an edge of SCK, and ``FROM_DESIGN`` for its source: the user corrects it from the HDL, says where it comes from, and checks it with ``stacv visualize edges spi_config.toml``.
  The comments give each edge's time for the periods on the command line.
* The timing reports are named by the interface and the signal, such as ``timing_reports/SPI.COPI_timing.rpt``.
* The part's values, and the fastest SCK each pin allows, are ``FROM_DATASHEET``, which stacv stops on until they are filled in (part_config_011).
  The part pins are named ``SCK``, ``COPI``, ``CS`` and ``CIPO``; rename them to the datasheet's.
* The trace delays are left for the user.
* Each table of the part and traces files is split by a line, ``#--- set by stacv create template spi; do not change below ---``.
  Above it is what the user fills in or renames; below it is what the command line set, such as the methodology, the signal and the edges of the part's pins.
  To change those, create the files again.

``example/spi_template`` holds the files of the command above.

Errors
------

``stacv create template`` does not overwrite an existing file, because a filled-in file cannot be created again.
It stops with an error, and writes nothing, when the file named by ``--output`` already exists, or for ``spi``, when any of the three files exists in the directory (create_001).
An SPI option given to another template is an error (create_002), and so is an ``spi`` template without ``--wires``, ``--mode`` or ``--type`` (create_003).
