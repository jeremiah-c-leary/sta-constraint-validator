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

Errors
------

``stacv create template`` does not overwrite an existing file, because a filled-in file cannot be created again.
It stops with an error, and writes nothing, when the file named by ``--output`` already exists (create_001).
