Part File
=========

The part file describes the timing of the part, the external device the FPGA or ASIC communicates with, as its datasheet gives it.
It is written once for each part, and can be used by every interface to that part.
The interface file names it with its ``part`` key.

.. code-block:: text

   stacv create template part --output part.toml

Delays are in nanoseconds and frequencies are in MHz.
Every key in the part file is required, and a key stacv does not read is an error (part_config_004); see :doc:`errors` for every error.

Properties
----------

.. code-block:: toml

   [properties]
   manufacturer = "MANUFACTURER"
   part_number = "PART_NUMBER"

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description
   * - ``manufacturer``
     - The name of the company that manufactures the part.
   * - ``part_number``
     - The manufacturer's part number of the part.

Datasheet
---------

.. code-block:: toml

   [datasheet]
   name = "DATASHEET_NAME"
   url = "DATASHEET_URL"
   version = "DATASHEET_VERSION"

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description
   * - ``name``
     - The name of the datasheet.
   * - ``url``
     - Where the datasheet can be found.
   * - ``version``
     - The version of the datasheet.

The datasheet is listed in the References section of the constraints file, so a reviewer can check every value against it.

Interfaces
----------

Each interface of the part, as the manufacturer names it, has an ``[[interface]]`` table.

.. code-block:: toml

   [[interface]]
   name = "INTERFACE_NAME"

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description
   * - ``name``
     - The name of the interface, as the manufacturer names it.

Pins
----

Each pin of an interface has an ``[[interface.pin]]`` table, after its ``[[interface]]`` table.
Pins are described from the part's point of view.

.. code-block:: toml

   # A part input:  the part captures the data.
   [[interface.pin]]
   name = "DATA_IN"
   methodology = "SDR-SS-I"
   clock = {pin = "CLK", max_frequency = 25}
   capture_edge = "Falling"
   setup = {value = 10, symbol = "tSetup", source = "Table X"}
   hold = {value = 10, symbol = "tHold", source = "Table X"}

   # A part output:  the part launches the data on the clock it receives.
   [[interface.pin]]
   name = "DATA_OUT"
   methodology = "SDR-SS-RT"
   clock = {pin = "CLK", max_frequency = 12.5}
   cko_max = {value = 30, symbol = "tCkoMax", source = "Table Z"}
   cko_min = {value = 0, symbol = "tCkoMin", source = "Table Z"}
   launch_edge = "Rising"

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description
   * - ``name``
     - The name of the pin.
       Each pin name is used once in the part, in every interface, since traces name a pin without its interface (part_config_007).
   * - ``methodology``
     - The :doc:`methodology <methodology>` of the pin.
       It decides the timing keys the pin has:

       * ``SDR-SS-I``: ``capture_edge``, ``setup``, ``hold``
       * ``SDR-SS-O``, ``SDR-SS-RT``: ``launch_edge``, ``cko_max``, ``cko_min``
   * - ``clock``
     - The clock pin of the part the data is captured or launched on:

       * ``pin``: the name of the clock pin.
       * ``max_frequency``: the maximum frequency of the clock for this pin, in MHz, greater than 0 (part_config_008).
   * - ``capture_edge``
     - The clock edge the part captures the data on: ``"Rising"`` or ``"Falling"`` (part_config_006).
   * - ``launch_edge``
     - The clock edge the part launches the data on: ``"Rising"`` or ``"Falling"`` (part_config_006).
   * - ``setup``
     - The setup requirement of the pin.
   * - ``hold``
     - The hold requirement of the pin.
   * - ``cko_max``
     - The maximum clock-to-out delay of the pin.
   * - ``cko_min``
     - The minimum clock-to-out delay of the pin.

``setup``, ``hold``, ``cko_max`` and ``cko_min`` each have the same keys:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description
   * - ``value``
     - The value from the datasheet.
   * - ``symbol``
     - The symbol of the value in the datasheet, such as ``tSU``.
   * - ``source``
     - Where in the datasheet the value comes from, such as a table number.
