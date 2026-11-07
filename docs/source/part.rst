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
   * - ``if_standard``
     - Optional: the interface standard the part interface follows, such as ``"SPI mode 1"`` (see :doc:`standards`).
   * - ``if_role``
     - With ``if_standard``: the part's role in the standard, ``"controller"`` or ``"peripheral"``.

A part with modes, such as a PHY with MII, RMII and RGMII, has one ``[[interface]]`` for each mode.
The interface file names the one it uses with ``part_interface`` (see :doc:`interface`), and pins are looked up in that interface only.
A ``part_interface`` the part does not have is an error (part_config_009).
The VSC8540ET in ``example/microchip/vsc8540et`` is a part with five interfaces.

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
   methodology = "SDR-SS-RT-DO"
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
     - The name of the pin, as the datasheet names it in the interface's mode.
       A bus is written ``NAME[upper:lower]``, such as ``TXD[3:0]``.
       Interfaces may share pin names; within an interface a pin is used once for each methodology (part_config_007), so a bidirectional pin, such as MDIO, has a table for each direction.
   * - ``if_signal``
     - Optional: the signal of the interface standard the pin carries, such as ``"COPI"`` (see :doc:`standards`).
   * - ``methodology``
     - The :doc:`methodology <methodology>` of the pin, from the part's view.
       A pin without a methodology is a clock pin: it gives only ``name`` and ``if_signal``, carries no timing, and the other pins name it as their clock.
       It decides the timing keys the pin has:

       * inputs, ``SDR-SS-I``, ``SDR-SS-RT-DI``, ``SDR-SYS-I``, ``DDR-SS-I``: ``capture_edge``, ``setup`` and ``hold``
       * outputs, ``SDR-SS-O``, ``SDR-SS-O-FLC``, ``SDR-SS-RT-DO``, ``SDR-SYS-O``, ``DDR-SS-O``: ``launch_edge``, and ``cko_max`` and ``cko_min``, or ``valid_before`` and ``valid_after``

       ``SDR-SS-O-FLC`` is an output timed to the first and last edges of a clock that stops, such as a chip select from a device's :doc:`datasheet <datasheet>`: ``valid_before`` is before the first edge and ``valid_after`` after the last.
       No interface methodology times it yet, so its port is deferred.

       An output gives its timing in exactly one form, the form its datasheet uses (part_config_010).
       An input gives the receiver's real setup and hold; a skew window, such as RGMII v1.3's tSKEWR, is a board budget and not a requirement of the pin.
   * - ``clock``
     - The clock pin of the part the data is captured or launched on:

       * ``pin``: the name of the clock pin.
       * ``max_frequency``: the maximum frequency of the clock for this pin, in MHz, greater than 0 (part_config_008).
       * ``duty_cycle``: optional, ``{min = ..., max = ...}`` in percent, for double data rate pins.
   * - ``capture_edge``
     - The clock edge the part captures the data on: ``"Rising"``, ``"Falling"``, or ``"Both"`` for double data rate (part_config_006).
   * - ``launch_edge``
     - The clock edge the part launches the data on: ``"Rising"``, ``"Falling"``, or ``"Both"`` for double data rate (part_config_006).
   * - ``setup``
     - The setup requirement of the pin, from the datasheet's Min column.
   * - ``hold``
     - The hold requirement of the pin, from the datasheet's Min column.
   * - ``cko_max``
     - The maximum clock-to-out delay of the pin.
   * - ``cko_min``
     - The minimum clock-to-out delay of the pin.
   * - ``valid_before``, ``valid_after``
     - The time the data is valid before and after the clock edge, for a clock centred in the data.
       stacv takes clock to out minimum = ``valid_after`` and maximum = the time between data changes - ``valid_before``.

The time between data changes is the period of the interface's clock, or half of it for double data rate.
Each conversion is written out in the constraints file, next to the constraint it gives.

A window only gives the time the data is guaranteed valid.
A datasheet that writes the window for a faster clock leaves the data far more time to change than it really takes.
The compensated RGMII outputs of the VSC8540ET are an example: the window is written for gigabit timing, so the part file gives the clock to out instead, worked out in its comments from the data's launch skew and the PHY's clock delay.

``setup``, ``hold``, ``cko_max``, ``cko_min`` and the window keys each have the same keys:

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
