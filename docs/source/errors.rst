Errors
======

stacv stops with an error when an input file is wrong, or when it cannot do what it was asked.
An error is not a rule failure: a rule failure means the timing reports were checked and something is wrong with the timing (see :doc:`trc`).

Every error is printed on one line to standard error, and stacv exits with code 2:

.. code-block:: text

   ERROR: [<identifier>] <file> <message>

* The identifier never changes, so it can be searched for.
* The file is the input file the error is in, as it was given or named.
* The message names the key and where it is, such as ``in port O_DATA`` or ``of clock clk_25mhz``, and, after a semicolon, how to correct it when that is not plain.

stacv visualize edges
---------------------

``stacv visualize edges`` is used to find the right edges, so it stops only for what it cannot draw:

* It reads only the interface file.
  The part and traces files do not need to exist yet, and the timing report paths are not read.
  An SPI configuration file also reads the part file once it exists, to find the part's SPI interface (spi_config_012, spi_config_013).
* Errors marked **Stops** in the interface table stop it, as they stop every command.
* Errors marked **Drawn** do not stop it.
  The port is drawn, and the error is printed under its requirements, on standard output, in the port's section.
  stacv still exits with code 2.
* Errors marked **-** are not checked by it.

Every other command stops on every error.

Interface file
--------------

.. list-table::
   :header-rows: 1
   :widths: 18 44 26 12

   * - Identifier
     - Message
     - Correction
     - visualize edges
   * - interface_config_001
     - ``is not valid TOML: <reason>``
     - Correct the TOML syntax at the line given.
     - Stops
   * - interface_config_002
     - ``missing required key "<key>"<location>``
     - Add the key.
       Also used for the keys of each ``[[clock]]``, ``generator``, ``launch_clock`` and ``capture_clock`` table.
     - Stops
   * - interface_config_003
     - ``key "<key>"<location> must be <type>``
     - Write the value as the type given, such as ``a non-empty string`` or ``a number``.
       Also used for every key of every table.
     - Stops
   * - interface_config_004
     - ``key "<key>"<location> is not a key stacv reads; the keys are <keys>``
     - Correct the key name.
       A misspelled optional key, such as ``idel``, would otherwise be ignored.
     - Stops
   * - interface_config_005
     - ``key "<key>"<location> uses environment variables that are not set: <names>``
     - Set the environment variables.
       For ``timing_reports``, only ``stacv check`` needs them.
     - \-
   * - interface_config_006
     - ``key "<key>"<location> names a file that does not exist: <path>``
     - Correct the path, or create the file.
       Paths are relative to the interface file.
     - \-
   * - interface_config_007
     - ``does not exist``
     - Correct the interface file name.
     - Stops
   * - interface_config_008
     - ``key "<key>"<location> names clock <name>, which no [[clock]] table defines``
     - Correct the clock name, or add its ``[[clock]]`` table.
     - Stops
   * - interface_config_009
     - ``clock <name> is defined by more than one [[clock]] table``
     - Remove or rename one of the tables.
     - Stops
   * - interface_config_010
     - ``key "status"<location> must be "analyze" or "defer"``
     - Correct the status.
     - Stops
   * - interface_config_011
     - ``key "methodology"<location> names <methodology>, which stacv does not support; correct it, or defer the port with status = "defer"``
     - Correct the methodology, or defer the port.
     - Stops
   * - interface_config_012
     - ``key "idle" of clock <name> must be "low" or "high"``
     - Correct the idle level.
     - Stops
   * - interface_config_013
     - ``key "capture_clock"<location> names clock <name>, which has no key "idle"; <methodology> is timed to the first and last edges of a clock that stops``
     - Add ``idle`` to the capture clock.
     - Stops
   * - interface_config_014
     - ``key "<key>"<location> has <edge> <value>; launch edges are numbers: 0, 1, 2, ...``
     - Write the launch edge as a whole number, even for a rising edge and odd for a falling edge.
     - Stops
   * - interface_config_015
     - ``key "<key>"<location> has <edge> <value>; capture edges are numbers: 0, 1, 2, ...``
     - Write the capture edge as a number on its clock, 0, 2, 4, ... for a rising edge and 1, 3, 5, ... for a falling edge.
     - Stops
   * - interface_config_016
     - ``key "period" of clock <name> must be greater than 0``
     - Correct the period, in nanoseconds.
     - Stops
   * - interface_config_017
     - ``port <name> with methodology <methodology> is defined by more than one [[port]] table``
     - Remove or rename one of the tables.
       A port can appear once for each methodology, such as a bidirectional port timed as an output and as a round trip.
     - Stops
   * - interface_config_018
     - ``key "capture_clock"<location> has setup_edge <edge> and hold_edge <edge>, which are not the same edge type``
     - The part captures on one edge type: make both edges rising or both falling.
       Was generate_006.
     - Drawn
   * - interface_config_019
     - ``key "launch_clock"<location> has setup_edge <edge> and hold_edge <edge>; an SDR-SS-O port launches each bit once, so both must be the same edge (a signal timed to the first and last clock edges is SDR-SS-O-FLC)``
     - Use the same launch edge, or use SDR-SS-O-FLC for a chip select.
     - Drawn
   * - interface_config_020
     - ``key "capture_clock"<location> has setup_edge <edge> and hold_edge <edge>; the hold edge of an SDR-SS-O port is the previous capture edge of the same type, <edge>``, or ``..., so setup_edge must be 2 or later`` when the setup edge is 0 or 1
     - Use the edge given.
       Not reported when interface_config_018 is.
     - Drawn
   * - interface_config_021
     - ``key "<clock key>"<location> names clock <name>, which has no key "port"; the <clock> leaves the device on a port``
     - Add the ``port`` the clock leaves the device on.
       The clock is the one the device forwards to the part: the capture clock of an SDR-SS-O or SDR-SS-O-FLC port, and the launch clock of an SDR-SS-RT-DI port.
     - \-
   * - interface_config_022
     - ``port <name> is not a port name or a bus written NAME[upper:lower]; give each bit its own [[port]], write the bus as NAME[upper:lower], or defer it``
     - A bus is written ``NAME[upper:lower]``, such as ``O_MII_TXD[3:0]``; a single bit or a wildcard is not a port name.
       Only an analyzed port is checked.
     - Stops
   * - interface_config_023
     - ``the edges<location> give a setup requirement of <time> and a hold requirement of <time>; <description>, so they must be <time> and <time>``
     - The edges do not match the edge the methodology captures on.
       A DDR-SS-I-SE port captures each bit on the edge it is aligned with: a setup requirement of 0 ns and a hold requirement of minus half a period, such as launch edge 2 to capture edges 2 and 1.
       A DDR-SS-I-NE port captures each bit on the edge after the one it is launched on: a setup requirement of half a period and a hold requirement of 0 ns, such as launch edge 0 to capture edges 1 and 0.
       Correct the edges, or use the other methodology.
     - Drawn
   * - interface_config_024
     - ``pin <pin> (<methodology>) of part interface <interface> has no port; add a [[port]] for it, named <device pin> after its trace, or a deferred one``
     - Every pin of the part interface needs a port, so no pin is left out of the timing unseen.
       The pin's trace names the port; when a shared traces file has several traces to the pin, each device pin is named.
       A deferred port covers the pin, unless it names a methodology that times another kind of pin.
       Reported by ``check``, ``generate xdc``, ``visualize block_diagram`` and ``visualize eye``, the commands that read the part and traces files.
     - Stops

Locations are ``in port <name>`` for a ``[[port]]`` table, or ``in port number <n>`` when the port has no name, ``of clock <name>`` or ``of clock number <n>`` for a ``[[clock]]`` table, ``in generator of clock <name>``, and ``in launch_clock of port <name>`` or ``in capture_clock of port <name>``.
Unknown keys are reported before missing keys, so a misspelled key is named as such.
The keys of a deferred port are not checked.

Traces file
-----------

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - traces_config_001
     - ``is not valid TOML: <reason>``
     - Correct the TOML syntax at the line given.
   * - traces_config_002
     - ``missing required key "<key>"<location>``
     - Add the key.
       Also used when there is no ``[[trace]]`` table.
   * - traces_config_003
     - ``key "<key>"<location> must be <type>``
     - Write the value as the type given.
   * - traces_config_004
     - ``key "<key>"<location> is not a key stacv reads; the keys are <keys>``
     - Correct the key name.
   * - traces_config_005
     - ``trace <name> has no delays in key "<key>" and no default_delay is defined``
     - Give the delays, or add ``default_delay``.
   * - traces_config_006
     - ``trace <name> key "<key>" must give both max_delay and min_delay, or neither``
     - Give both delays, or write ``{}`` to use ``default_delay``.
   * - traces_config_007
     - ``trace <name> has neither device_to_part nor part_to_device``, or ``has neither source_to_device nor source_to_part`` for a trace from a clock source
     - Give the direction the trace carries.
   * - traces_config_008
     - ``trace <name> key "<key>" has max_delay <value> less than min_delay <value>``, or ``default_delay has max_delay <value> less than min_delay <value>``
     - Correct the delays.
   * - traces_config_009
     - ``trace <name> is defined by more than one [[trace]] table``
     - Remove or rename one of the tables.
   * - traces_config_010
     - ``pin <pin> (<methodology>) of part interface <interface> has no trace to a device port; add a trace for it, and a [[port]] or a deferred port in the interface file``
     - Every pin of the part interface needs a trace to the device, from the device for a pin the part captures, and to it for a pin the part drives.
       Reported by ``check``, ``generate xdc``, ``visualize block_diagram`` and ``visualize eye``, with interface_config_024.
   * - traces_config_011
     - ``trace <name> gives if_signal and a pin; give if_signal, or device_pin and part_pin``, or ``trace <name> from a clock source gives if_signal; a trace from a clock source names its pin``
     - A trace names its ends with ``device_pin`` and ``part_pin``, or with the ``if_signal`` that links them (see :doc:`standards`).
   * - traces_config_012
     - ``key "<device_pin or part_pin>" of trace <name> is FROM_..._<name>; replace it with the name in your design or the part's datasheet``
     - Fill in the pin of a trace from a clock source, as a template writes it: the port the clock arrives on, or the part's clock pin.

The location is ``in trace <name>``, or ``in trace number <n>`` when the trace has no name.

Part file
---------

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - part_config_001
     - ``is not valid TOML: <reason>``
     - Correct the TOML syntax at the line given.
   * - part_config_002
     - ``missing required key "<key>"<location>``
     - Add the key.
       Every key in the part file is required.
   * - part_config_003
     - ``key "<key>"<location> must be <type>``
     - Write the value as the type given.
   * - part_config_004
     - ``key "<key>"<location> is not a key stacv reads; the keys are <keys>``
     - Correct the key name.
   * - part_config_005
     - ``key "methodology"<location> names <methodology>; a part pin is SDR-SS-I, SDR-SS-O, SDR-SS-O-FLC, SDR-SS-RT-DI, SDR-SS-RT-DO, SDR-SYS-I, SDR-SYS-O, DDR-SS-I or DDR-SS-O``
     - Correct the methodology.
   * - part_config_006
     - ``key "<key>"<location> must be "Rising", "Falling" or "Both"``
     - Correct the edge of ``capture_edge`` or ``launch_edge``.
       ``"Both"`` is for double data rate pins.
   * - part_config_007
     - ``pin <name> with methodology <methodology> is defined by more than one [[interface.pin]] table in interface <interface>``
     - Remove or rename one of the tables.
       Interfaces may share pin names, and a bidirectional pin has one table for each methodology.
   * - part_config_008
     - ``key "max_frequency"<location> must be greater than 0``
     - Correct the frequency, in MHz.
   * - part_config_009
     - ``has no interface named <name>, which key "part_interface" of the interface file names``
     - Correct ``part_interface`` in the interface file, or the interface's ``name`` in the part file.
   * - part_config_010
     - ``timing<location> must give cko_max and cko_min, or valid_before and valid_after``, for an output pin
     - Give the pin's timing in one form, the form its datasheet uses.
   * - part_config_011
     - ``key "<key>"<location> is FROM_DATASHEET_<name>; fill it in from the part's datasheet``
     - Fill in the ``value``, ``source`` or ``max_frequency`` a template left for the part's datasheet.
   * - part_config_012
     - ``key "clock"<location> must give pin or if_signal, not both``
     - Name the clock by its pin, or by the signal of its ``[[interface.clock_pin]]``.
   * - part_config_013
     - ``key "clock"<location> gives if_signal <signal>, which no [[interface.clock_pin]] of the interface gives``
     - Add the clock pin, or correct the signal.

The location is ``in [properties]``, ``in [datasheet]``, ``in interface <name>``, or ``in pin <name> of interface <name>``.

SPI configuration file
----------------------

These are checked by every command that reads an SPI configuration file (see :doc:`spi_config`).
The location names the table and the line of the key, such as ``in [cs] (line 54)``; a missing key is given the line of its table.
A file that is not valid TOML, or does not exist, is reported as interface_config_001 or interface_config_007, as stacv reads it before it knows its kind.

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - spi_config_002
     - ``missing required key "<key>"<location>``
     - Add the key, or the table.
   * - spi_config_003
     - ``key "<key>"<location> must be <type>``
     - Write the value as the type given, such as ``a non-empty string`` or ``a whole number``.
   * - spi_config_004
     - ``key "<key>"<location> is not a key stacv reads; the keys are <keys>``
     - Correct the key name.
   * - spi_config_005
     - ``key "interface"<location> names <name>, which stacv has no configuration for; the configurations are <names>``
     - Correct the name, or time the interface with an interface file.
   * - spi_config_006
     - ``key "<key>"<location> is FROM_DESIGN_<name>; replace it with the name in your design``, or ``key "<edge>"<location> has source FROM_DESIGN_<name>; say where in the design the edge comes from``
     - Fill in the name, or the place in the HDL the edge comes from.
   * - spi_config_007
     - ``key "mode"<location> must be 0, 1, 2 or 3``
     - Give the SPI mode.
   * - spi_config_008
     - ``key "role"<location> must be "controller"; a peripheral is not supported yet``
     - Only the device as the controller can be timed yet.
   * - spi_config_009
     - ``key "period"<location> must be greater than 0``
     - Give the period in ns.
   * - spi_config_010
     - ``key "period" in [sck]<line> is <time> ns, which is not an even number of device clock periods of <time> ns``, or the same for ``read_period``
     - Give an SCK period that is an even number of device clock periods, so each SCK edge is on a rising edge of the device clock.
   * - spi_config_011
     - ``key "<edge>"<location> puts the launch at edge <n>, ...``, or ``puts the setup capture`` or ``the hold capture``, and the edge it passes
     - Keep the edge in its range (see :doc:`spi_config`); check it with ``stacv visualize edges``.
   * - spi_config_012
     - ``key "part"<location> names <file>, which has no [[interface]] with if_standard "SPI mode <mode>" and if_role "peripheral"``
     - Give the part's SPI interface the mode and the peripheral role, or correct the mode.
   * - spi_config_013
     - ``key "part"<location> names <file>, which has more than one [[interface]] with ...: <names>``
     - Keep one SPI interface of the mode in the part file.
   * - spi_config_014
     - ``key "<edge>"<location> has sck_edge "<name>"; it must be <names>``
     - Count the edge from an SCK edge the key allows (see :doc:`spi_config`).
   * - spi_config_015
     - ``key "<edge>"<location> has clocks <n>; an edge is on a device clock edge, so clocks is a whole or half number``
     - Give the device clocks from the SCK edge; a half is a falling edge of the device clock.

RMII configuration file
-----------------------

These are checked by every command that reads an RMII configuration file (see :doc:`rmii_config`).
The location names the table and the line of the key, as for an SPI configuration file.

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - rmii_config_002
     - ``missing required key "<key>"<location>``
     - Add the key, or the table; only ``[tx_er]`` and ``[rx_er]`` may be left out.
   * - rmii_config_003
     - ``key "<key>"<location> must be <type>``
     - Write the value as the type given.
   * - rmii_config_004
     - ``key "<key>"<location> is not a key stacv reads; the keys are <keys>``
     - Correct the key name.
   * - rmii_config_006
     - ``key "<key>"<location> is FROM_DESIGN_<name>; replace it with the name in your design``
     - Fill in the name.
   * - rmii_config_008
     - ``key "role"<location> must be "MAC"; a PHY is not supported yet``
     - Only the device as the MAC can be timed yet.
   * - rmii_config_014
     - ``key "port"<location> is <port>; write a bus port as NAME[upper:lower], such as TXD[1:0], and its register as reg[*]``
     - Write the port as the bus it is; only its register is written with ``[*]``.
   * - rmii_config_012
     - ``key "part"<location> names <file>, which has no [[interface]] with if_standard "RMII" and if_role "PHY"``
     - Give the part's RMII interface the standard and the PHY role.
   * - rmii_config_013
     - ``key "part"<location> names <file>, which has more than one [[interface]] with ...: <names>``
     - Keep one RMII interface in the part file.

An ``interface`` that names a configuration stacv does not have is spi_config_005, which lists the configurations.

Interface standards
-------------------

These are checked by ``check``, ``generate xdc``, ``visualize block_diagram`` and ``visualize eye``, after the interface, traces and part files are read (see :doc:`standards`).
The file named is the one to correct.

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - if_standard_001
     - ``<clock, port or trace> gives if_signal <signal>, but the interface file names no if_standard``
     - Give ``if_standard`` in the interface file, or remove the signal.
   * - if_standard_002
     - ``key "if_standard" names <standard>; the standards are <standards>``
     - Correct the standard, in the interface file or the part interface.
   * - if_standard_003
     - ``<file> names if_standard <standard> but no if_role``, or ``key "if_role" names <role>; the roles of <standard> are <roles>``
     - Give the role of the device, or of the part.
   * - if_standard_004
     - ``<item> gives if_signal <signal>, which is not a signal of <standard>``, or ``... but <signal> does not repeat, so it is not numbered``
     - Correct the signal; only a signal that repeats, such as CS, is numbered: ``CS.1``.
   * - if_standard_005
     - ``<item> and <item> both give if_signal <signal>``, or ``... which another pin (trace) gives``
     - Give each port, part pin and trace its own signal; only clocks of one port share one.
   * - if_standard_006
     - ``part interface <name> names no if_standard``, ``follows <standard>, but the interface file follows <standard>``, or ``is the <role>, as is the device``
     - The part interface follows the interface file's standard, in the other role.
   * - if_standard_007
     - ``has no port or clock with if_signal <signal>, which trace <name> carries``, or ``clock <name> gives if_signal <signal> but no port``
     - Give the port or the clock the trace's signal, and the clock its port.
   * - if_standard_008
     - ``part interface <name> has no pin with if_signal <signal>, which trace <name> carries``
     - Give the part pin the trace's signal.
   * - if_standard_009
     - ``<file> has no <port or clock, pin, trace> with if_signal <signal>, a signal of <standard>``
     - Every signal of the standard needs a port or clock, a part pin and a trace; defer a port that is not timed yet.
   * - if_standard_010
     - ``trace <name> carries <signal>, which the <role> drives, and the device is the <role>, so the trace gives <direction> and not <direction>``
     - Give the trace the direction its signal goes.
   * - if_standard_011
     - ``port <name> carries <signal> ... so the port is an <input or output>; methodology <methodology> times an <output or input>``, or the same for a part pin
     - Correct the signal, or the methodology.
   * - if_standard_012
     - ``clock <name> idles <level>, but the clock of <standard> idles <level>``, ``port <name> uses <edge> edges of <clock>, but <standard> <samples or changes> data on <edge> edges``, or the same for a part pin's ``capture_edge`` or ``launch_edge``
     - Correct the mode, or the edges.

Generating constraints
----------------------

These are checked by ``stacv generate`` for each analyzed port, after the input files are read.
The message starts with the port: ``ERROR: [<identifier>] port <name> <message>``.

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - generate_001
     - ``capture clock <name> has no generator``, or ``launch clock <name> has no generator`` for an SDR-SS-RT-DI port
     - Add the ``generator`` of the clock the device forwards to the part.
   * - generate_002
     - ``setup requirement <time>ns is not a whole number of <time>ns step periods``
     - Choose edges whose setup requirement is a whole number of launch periods.
   * - generate_003
     - ``hold requirement <time>ns is not a whole number of <time>ns step periods``
     - Choose edges whose hold requirement is a whole number of launch periods.
   * - generate_004
     - ``setup multicycle <n> is less than 0``
     - The setup capture edge must not be before the setup launch edge.
       A setup capture edge at the same time as the launch edge is allowed: the data is captured by the edge that launches it.
   * - generate_005
     - ``hold multicycle <n> is less than 0``
     - The hold capture edge is too late for the setup edges.
   * - generate_006
     - Moved to interface_config_018.
     - The identifier is not used again.
   * - generate_007
     - ``has no trace from the device to the part``, or ``has no trace from the part to the device`` for an SDR-SS-RT-DI port
     - Add the port's trace, with ``device_to_part`` for an output and ``part_to_device`` for an SDR-SS-RT-DI port.
   * - generate_008
     - ``trace <name> ends at pin <pin>, which the part does not have``, or ``starts at pin`` for an SDR-SS-RT-DI port
     - Correct the trace's ``part_pin``, or add the pin to the part.
   * - generate_009
     - ``has no clock trace from <port> to part pin <pin>``
     - Add the clock trace.
   * - generate_010
     - ``has <n> timing reports; the report script writes one file for each port``
     - Give the port one timing report for ``stacv generate report_tcl``.
   * - generate_011
     - ``launch edge <n> at <time> is not at an edge of <clock>; the datasheet gives the clock to out from the clock edge the data is launched with``, or ``setup launch edge <n> is at a <rising or falling> edge of <clock> and hold launch edge <n> at a <falling or rising> edge; the datasheet gives the clock to out from one edge``, for an SDR-SS-O port by ``stacv generate datasheet``
     - Launch the data at an edge of the clock the device forwards, the same kind of edge for setup and hold.
   * - generate_012
     - ``<file> is an interface file, not an interface configuration file; ...``, by ``stacv generate interface``.
       The message starts with the file, not a port.
     - Give an interface configuration file, such as ``spi_config.toml``.

Creating templates
------------------

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - create_001
     - ``<file> already exists; the template is not written``
     - Choose another file name, or remove the file.
       For ``spi``, no file is written when any of the three exists.
   * - create_002
     - ``--<option> is an option of the spi template, not of the <file type> template``
     - Leave the SPI options out of the interface, traces and part templates.
   * - create_003
     - ``the spi template needs --<option>``
     - Give ``--wires``, ``--mode`` and ``--type``.
   * - create_004
     - ``--wires 3 is not supported yet``, or ``--type peripheral is not supported yet``
     - Only a 4-wire SPI controller can be created yet.
   * - create_005
     - ``--clock-period and --sck-period must be greater than 0``, or ``--sck-period <period> is not an even number of --clock-period <period>``
     - Give an SCK period that is an even number of device clock periods, so each SCK edge is on a rising edge of the device clock.

Timing reports
--------------

These are checked by ``stacv check`` while it reads each timing report.
The file is followed by the line the error is on: ``ERROR: [<identifier>] <file>:<line> <message>``.

.. list-table::
   :header-rows: 1
   :widths: 18 52 30

   * - Identifier
     - Message
     - Correction
   * - vivado_tr_parse_001
     - ``has no timing reports``
     - Write the file with the report script.
   * - vivado_tr_parse_002
     - ``has the end of a timing report without its beginning``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_003
     - ``has the beginning of a timing report without its end``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_004
     - ``timing report has no "Path Type:"``
     - Write the report with ``report_timing -path full_clock_expanded``.
   * - vivado_tr_parse_005
     - ``"Path Type:" must be Max or Min``
     - Write setup and hold reports only.
   * - vivado_tr_parse_006
     - ``timing report has no "Source:"``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_007
     - ``timing report has no "Destination:"``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_008
     - ``"Path Type:" must name the Slow or Fast process corner``
     - Write the reports at the Slow and Fast corners, with ``config_timing_corners``.
   * - vivado_tr_parse_009
     - ``has no clock name after "clocked by"``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_010
     - ``clock has no period``, ``clock period must be in ns``, or ``clock period must be greater than 0``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_011
     - ``timing report must have 4 or 5 separator lines, but has <n>; write it with report_timing -column_style variable_width``
     - Write the report as the message says.
   * - vivado_tr_parse_012
     - ``timing report has no "Clock Pessimism Removal (CPR):"``, or ``"Clock Pessimism Removal (CPR):" has no value``
     - Write the report with ``report_timing -path full_clock_expanded``.
   * - vivado_tr_parse_013
     - ``timing report has no "Output Delay:" or "Input Delay:"``, or ``"Output Delay:" has no value``, or ``"Input Delay:" has no value``
     - The report is not to an output port or from an input port; check the port name.
   * - vivado_tr_parse_014
     - ``"Clock Uncertainty:" has no value``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_015
     - ``"<key>" must be in ns``
     - The file is incomplete or edited; write it again.
       Used for every time except the clock period, which is vivado_tr_parse_010.
   * - vivado_tr_parse_016
     - ``slack must be a number of ns``
     - The file is incomplete or edited; write it again.
   * - vivado_tr_parse_017
     - ``timing report is of a path the constraints do not time, such as a false path; report only the paths between the port and registers``
     - The report starts ``Slack:`` with no result, as Vivado writes a false path.
       Write the reports with the script ``stacv generate report_tcl`` writes, which asks only for the paths between the port and registers.
   * - vivado_tr_parse_018
     - ``timing report's path starts and ends at the same point <name>; report the paths between the port and registers``
     - A path from a point to itself times nothing, such as the path through a bidirectional pad from its input to its output.
       Write the reports with the script ``stacv generate report_tcl`` writes, which leaves such paths out.
