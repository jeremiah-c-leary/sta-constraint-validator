Interface File
==============

The interface file describes one interface between the device and a part: its clocks, its ports, and where the part, traces and timing reports are.
It is the file every stacv command reads.

.. code-block:: text

   stacv create template interface --output interface.toml

Periods are in nanoseconds.
Paths are relative to the interface file, and can use environment variables such as ``$PROJ_DIR``.
An environment variable that is not set is an error (interface_config_005).
A key stacv does not read, such as a misspelled ``idel``, is an error (interface_config_004), except in a deferred port (see :doc:`errors`).
The variables in ``timing_reports`` are needed only by ``stacv check``, which reads the reports.
The other commands run without them.

Top level
---------

.. code-block:: toml

   description = "INTERFACE_DESCRIPTION"
   name = "INTERFACE_NAME"
   part = "part.toml"
   traces = "traces.toml"

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Key
     - Required
     - Description
   * - ``description``
     - Yes
     - A brief description of the interface.
   * - ``name``
     - Yes
     - The name of the interface.
       It is shown in the headers of the generated constraints file and report script.
   * - ``part``
     - Yes
     - The path of the :doc:`part file <part>` of the part this interface connects to.
   * - ``part_interface``
     - Yes
     - The ``[[interface]]`` of the part this interface uses, such as ``"MII"`` for a PHY with several modes.
       Its pins are the only pins looked up, so a pin of another mode is never used by mistake.
   * - ``traces``
     - Yes
     - The path of the :doc:`traces file <traces>` that describes the connections between the device and the part.
   * - ``if_standard``
     - No
     - The interface standard the interface follows, such as ``"SPI mode 1"`` (see :doc:`standards`).
   * - ``if_role``
     - With ``if_standard``
     - The device's role in the standard: ``"controller"`` or ``"peripheral"``.

A missing key is an error (interface_config_002), and so is a path to a file that does not exist (interface_config_006).

Clocks
------

Each clock of the interface is defined once, in a ``[[clock]]`` table.
Ports refer to clocks by name.

.. code-block:: toml

   [[clock]]
   name = "clk_100mhz"
   period = 10.000

   [[clock]]
   name = "clk_25mhz"
   period = 40.000
   port = "O_CLK"
   idle = "low"
   generator = {source = "DEVICE_ELEMENT", master_pin = "MASTER_PIN", target_pin = "TARGET_PIN", master_clock = "clk_100mhz"}

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Key
     - Required
     - Description
   * - ``name``
     - Yes
     - The name of the clock in the timing reports.
       Each clock name is defined once (interface_config_009).
   * - ``period``
     - Yes
     - The period of the clock in nanoseconds, greater than 0 (interface_config_016).
   * - ``port``
     - No
     - The device port the clock leaves the device on, to the part.
       Not used for a clock that stays inside the device.
       The clock the device forwards to the part needs it (interface_config_021): the capture clock of an SDR-SS-O or SDR-SS-O-FLC port, and the launch clock of an SDR-SS-RT-DI port.
       Two clocks can leave on the same port, such as a write clock and a slower read clock.
   * - ``idle``
     - No
     - The level of a clock that stops between transfers, such as an SPI clock: ``"low"`` or ``"high"`` (interface_config_012).
       Not used for a clock that runs all the time.
       An ``SDR-SS-O-FLC`` port needs it on its capture clock (interface_config_013).
   * - ``if_signal``
     - No
     - The signal of the interface standard the clock's port carries, such as ``"SCK"`` (see :doc:`standards`).
       Clocks of one port may share a signal; a clock inside the device gives none.
   * - ``generator``
     - No
     - The element in the device that generates the clock.
       Not used for a clock that stays inside the device.
       ``stacv generate xdc`` needs it on the clock every analyzed port forwards to the part (generate_001).

The ``generator`` table has these keys, all required:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description
   * - ``source``
     - The element in the device that generates the clock, such as the register that forwards it.
   * - ``master_pin``
     - The pin of the element the master clock arrives at.
   * - ``target_pin``
     - The pin of the element the generated clock leaves from.
   * - ``master_clock``
     - The clock at the master pin.
       It must be defined in a ``[[clock]]`` table (interface_config_008).

Ports
-----

Each port of the interface has a ``[[port]]`` table.
A port can have more than one table, one for each methodology, such as a bidirectional port; the same port and methodology twice is an error (interface_config_017).

.. code-block:: toml

   [[port]]
   status = "analyze"
   name = "O_DATA"
   methodology = "SDR-SS-O"
   launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}
   capture_clock = {name = "clk_25mhz", setup_edge = "D", hold_edge = "B"}
   registers = ["q_data_reg"]
   timing_reports = [
       "O_DATA_timing.rpt",
   ]

   [[port]]
   status = "defer"
   name = "I_DATA"

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Key
     - Required
     - Description
   * - ``status``
     - No
     - ``"analyze"``: the port is checked and its constraints are generated.
       This is the default when ``status`` is missing.

       ``"defer"``: the port is left for later.
       A deferred port needs only ``name`` and ``status``; any other keys are not read, except ``methodology``.

       Every pin of the part interface needs a port, analyzed or deferred, through its trace (interface_config_024).
       A deferred port is how a pin that is not timed yet is listed.

       Any other value is an error (interface_config_010).
   * - ``name``
     - Yes
     - The name of the port in the timing reports.
       A bus is written ``NAME[upper:lower]``, such as ``O_MII_TXD[3:0]``; any other bracket, or a wildcard, is an error (interface_config_022).
   * - ``methodology``
     - Yes
     - The :doc:`methodology <methodology>` of the port.
       An analyzed port is ``SDR-SS-O``, ``SDR-SS-O-FLC``, ``SDR-SS-RT-DI``, ``SDR-SS-I``, ``SDR-SS-RT-DO``, ``SDR-SYS-O``, ``SDR-SYS-I``, ``DDR-SS-O``, ``DDR-SS-I-SE`` or ``DDR-SS-I-NE``; a port with another methodology is deferred until stacv supports it (interface_config_011).
   * - ``if_signal``
     - No
     - The signal of the interface standard the port carries, such as ``"COPI"`` (see :doc:`standards`).
       A deferred port can give it too.
   * - ``registers``
     - Yes
     - The registers that drive the port, for an output, or capture it, for an input, such as ``["q_mdio_out_reg", "q_mdio_oe_reg"]``.
       ``*`` matches any characters, such as ``q_txd_reg[*]`` for every bit of a bus.
       Every path in the port's timing reports must start or end at one of them (s0_register_001), and each one must be in a timing report (s0_register_002).
   * - ``launch_clock``
     - Yes
     - The clock that launches the data, and its edges.
   * - ``capture_clock``
     - Yes
     - The clock that captures the data, and its edges.
   * - ``timing_reports``
     - Yes
     - A list of the timing reports of the port.
       ``stacv check`` reads any number of reports; ``stacv generate report_tcl`` writes exactly one for each port (generate_010).

``launch_clock`` and ``capture_clock`` have these keys, all required:

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Key
     - Description
   * - ``name``
     - The name of a clock defined in a ``[[clock]]`` table (interface_config_008).
   * - ``setup_edge``
     - The edge of the setup check.
   * - ``hold_edge``
     - The edge of the hold check.

Edges
^^^^^

Edges are counted from the first rising edge of each clock, at time 0:

* Launch edges are numbers: 0, 2, 4, ... are rising edges and 1, 3, 5, ... are falling edges.
* Capture edges are letters: A, C, E, ... are rising edges and B, D, F, ... are falling edges.

A launch edge written as a letter, or a capture edge written as a number, is an error (interface_config_014, interface_config_015).
The setup and hold capture edges must be the same type, both rising or both falling, because the part captures on one edge type (interface_config_018).

An SDR-SS-O port has two more rules:

* The launch setup and hold edges are the same edge, because each bit is launched once (interface_config_019).
* The capture hold edge is the capture edge of the same type before the setup edge, one capture clock period earlier, such as ``"B"`` for ``"D"`` (interface_config_020).

The edges of an SDR-SS-O-FLC port are independent, so these two rules do not apply to it (see :doc:`methodology`).

``stacv visualize edges`` still draws a port whose edges break these rules, and prints the error under the port's requirements, so the drawing can be used to correct them.
Every other command stops on the error.

Edge *n* of a clock is at (period / 2) × *n*, so the setup requirement is the time of the capture setup edge minus the time of the launch setup edge, and the hold requirement is the time of the capture hold edge minus the time of the launch hold edge.
Check the edges with ``stacv visualize edges`` before generating the constraints.
It reads only the interface file, so it can be run before the part and traces files are written, and their paths are not checked.
