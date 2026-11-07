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

``stacv create template spi`` creates all three files of an SPI interface, linked by the SPI signals (see :doc:`standards` and :doc:`spi`):

.. code-block:: text

   stacv create template spi --wires 4 --mode 0 --type controller --clock-period 10 --sck-period 40 --output spi

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

``interface.toml``, ``part.toml`` and ``traces.toml`` are written to the directory, which is created when it does not exist.
The command each was created by is at its top.

* The mode sets the level SCK idles at, and the clock periods and the mode set every launch and capture edge, so the user only checks them with ``stacv visualize edges``.
* The ports are named by their role: ``O_SPI_SCK``, ``O_SPI_COPI``, ``O_SPI_CS`` and ``I_SPI_CIPO``, and the part pins ``SCK``, ``COPI``, ``CS`` and ``CIPO``.
* The timing reports are named by the interface and the signal, such as ``timing_reports/SPI_INTERFACE_NAME.COPI_timing.rpt``, so renaming ``SPI_INTERFACE_NAME`` everywhere it appears renames them too.
* The part's values are ``FROM_DATASHEET``, which stacv stops on until they are filled in (part_config_011).
* The registers and the trace delays are left for the user.

``example/spi_template`` holds the files of the command above.

Errors
------

``stacv create template`` does not overwrite an existing file, because a filled-in file cannot be created again.
It stops with an error, and writes nothing, when the file named by ``--output`` already exists, or for ``spi``, when any of the three files exists in the directory (create_001).
An SPI option given to another template is an error (create_002), and so is an ``spi`` template without ``--wires``, ``--mode`` or ``--type`` (create_003).
