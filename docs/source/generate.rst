Generating Constraints
======================

stacv generates the timing constraints of an interface, and the script that writes its timing reports, from the same files it uses to check the timing reports.
The constraints, the visualizations and the checks all come from one interface file, so the generated constraints time the edges and delays the checks expect.

.. code-block:: text

   stacv generate xdc interface.toml
   stacv generate xdc interface.toml --output constraints.xdc
   stacv generate report_tcl interface.toml --output report.tcl
   stacv generate datasheet interface.toml --output datasheet.toml
   stacv generate interface spi_config.toml --output interface.toml

The ``xdc`` target writes a Vivado constraints file for the interface.
The ``report_tcl`` target writes a Vivado script that writes the timing reports ``stacv check`` reads.
The ``datasheet`` target writes the timing of each port at the device's pins, from the timing reports (see :doc:`datasheet`).
The ``interface`` target writes the interface file an interface configuration file expands to (see :doc:`spi_config`).
Every target reads an interface configuration file, such as ``spi_config.toml``, in place of an interface file.
Each is written to standard output, or to the file named by ``--output``.
An ``sdc`` target is planned for other vendors.

The intended process is:

#. Create the interface, traces and part files from their templates with ``stacv create template``, and fill them in; for SPI, the SPI configuration, traces and part files.
#. Confirm the launch and capture edges with ``stacv visualize edges``.
#. Generate the constraints and apply them in the timing tool.
#. Generate the report script and source it in the timing tool.
#. Run the timing reports back through ``stacv check``.

The checks confirm the timing tool applied the constraints as intended.
The DAC81404 example in ``example/texas_instruments/DAC81404`` goes through the whole process.
``if_dac81404.xdc`` is its generated constraints file, and ``if_dac81404_stacv_report.tcl`` is its generated report script, both generated in the example's directory.
Its timing reports are under ``$PROJ_DIR``, so run it from the project directory with ``PROJ_DIR`` set:

.. code-block:: text

   export PROJ_DIR=$(pwd)
   stacv check example/texas_instruments/DAC81404/interface.toml

Applies to
----------

SDR-SS-O.
Other methodologies are added as they are supported by the checks.

Interface file
--------------

Clocks
^^^^^^

Each clock of the interface is defined once, in a ``[[clock]]`` table, and ports refer to it by name:

.. code-block:: toml

   [[clock]]
   name = "clk_100mhz"
   period = 10.000

   [[clock]]
   name = "dac_sclk"
   period = 40.000
   port = "O_DAC_SCLK"
   generator = {source = "q_spi_output_clock_reg", master_pin = "C", target_pin = "Q", master_clock = "clk_100mhz"}

   [[port]]
   name = "O_DAC_DATA"
   methodology = "SDR-SS-O"
   launch_clock = {name = "clk_100mhz", setup_edge = 8, hold_edge = 8}
   capture_clock = {name = "dac_sclk", setup_edge = "D", hold_edge = "B"}

``generator`` names the element that generates the clock: the register that forwards the clock, a clock manager, or anything else that drives the clock port.
It also tells a reviewer where the forwarded clock comes from.

:source: The cell that generates the clock.
:master_pin: The pin of the cell the master clock arrives at.
:target_pin: The pin of the cell the generated clock leaves from.
:master_clock: The clock at the master pin.

``generator`` is optional for ``stacv check`` and ``stacv visualize``.
``stacv generate`` stops with an error if the clock an analyzed port forwards to the part has none.

Port status
^^^^^^^^^^^

A port can be timed one at a time with the optional ``status`` key:

:analyze: The port is checked and its constraints are generated.
          This is the default when ``status`` is missing.
:defer: The port is left for later.
        It only needs its ``name`` and ``status``.

A deferred port is drawn in the block diagram and listed in the constraints file as deferred, but no constraints are generated for it.
An analyzed port must use a methodology stacv supports; a port that cannot be analyzed yet is deferred.

Traces file
-----------

When the delay of a trace is not known yet, its delays are left empty and the default delay is used:

.. code-block:: toml

   default_delay = {max_delay = 1.0, min_delay = 0.0}

   [[trace]]
   name = "chip_select"
   device_pin = "O_DAC_CSF"
   part_pin = "CSF"
   device_to_part = {}

Delays taken from the default are marked in the constraints file, so they are not mistaken for measured delays.

Assumptions
-----------

* The clock that stays in the device is defined by the design, so it is not generated:
  the launch clock of an SDR-SS-O or SDR-SS-O-FLC port, and the capture clock of an SDR-SS-RT-DI port.
* Both clocks have a 50% duty cycle.
* The longer period is an integer multiple of the shorter period.

Clocks with other duty cycles are not supported.
They will be added if they are requested.

Constraints
-----------

Generated clock
^^^^^^^^^^^^^^^

Each clock the device forwards to the part is generated once, on its generator, in the order the ports first use it.
That is the capture clock of an SDR-SS-O or SDR-SS-O-FLC port, and the launch clock of an SDR-SS-RT-DI port.

:Name: The name of the clock.
:Source: ``generator.source`` / ``generator.master_pin``
:Object: ``generator.source`` / ``generator.target_pin``
:Ratio: Divide by clock period / master clock period when the clock is slower.
        Multiply by master clock period / clock period when the clock is faster.
:Add: ``-add`` when a clock is already generated at the same ``source`` and ``target_pin``.
      Without it, the second clock would replace the first.
      Vivado needs the master clock of a clock generated with ``-add``, so ``-master_clock`` names ``generator.master_clock``.

The generated clock is defined where it is generated, not on the clock port.

Two clocks can be generated at the same pin, such as the DAC81404 write clock ``dac_sclk`` at 25 MHz and its read clock ``dac_sclk_rd`` at 12.5 MHz, the fastest SCLK the part allows for a read.

Output delays
^^^^^^^^^^^^^

Each port gets a maximum and a minimum output delay against the capture clock.
They are the values the stage 3 rules check:

:Maximum: data trace maximum delay - clock trace minimum delay + part setup
:Minimum: data trace minimum delay - clock trace maximum delay - part hold

The output delays use the clock port as their reference pin.
The generated clock is defined at the target pin of its generator, so without the reference pin, the delay from the target pin to the clock port is left out of the clock path.
The timing report is then wrong without any warning.

When the capture edges are falling edges (B, D, F, ...), the output delays are applied to the falling edge of the capture clock.

Input delays
^^^^^^^^^^^^

An SDR-SS-RT-DI port gets a maximum and a minimum input delay against its launch clock, the clock the device forwards to the part.
The clock goes out to the part, the part launches the data, and the data comes back:

:Maximum: clock trace maximum delay + part clock to out maximum (``cko_max``) + data trace maximum delay
:Minimum: clock trace minimum delay + part clock to out minimum (``cko_min``) + data trace minimum delay

The data trace is the port's ``part_to_device`` trace.
Like the output delays, the input delays use the clock port as their reference pin, so the delay from the target pin of the generator to the clock port is in the launch clock path.

When the launch edges are falling edges (1, 3, 5, ...), the input delays are applied to the falling edge of the launch clock.

Multicycle paths
^^^^^^^^^^^^^^^^

The timing tool times the closest pair of launch and capture edges by default.
Multicycle paths move the setup and hold checks to the configured edges.
They are counted in cycles of the faster clock, the step clock:

* When the launch clock is faster, the multicycle paths move the launch edge (``-start``).
* Otherwise, they move the capture edge (``-end``).

The time of an edge is calculated the same way as in s4_requirement_001 and s4_requirement_002.
The setup requirement is the time of the capture setup edge minus the time of the launch setup edge.
The hold requirement is the time of the capture hold edge minus the time of the launch hold edge.

:Setup multicycle: setup requirement / step period
:Hold multicycle: (setup requirement - hold requirement) / step period - 1

A setup multicycle of 1 and a hold multicycle of 0 are the timing tool's default and are not written.
Each multicycle path applies from the launch clock to an output port, or from an SDR-SS-RT-DI port to its capture clock, so ports that share clocks can use different edges.

For example, a 10 ns launch clock and a 40 ns capture clock, with ``setup_edge = 4`` to ``"C"`` and ``hold_edge = 4`` to ``"A"``:

* The setup requirement is 40 - 20 = 20 ns, a setup multicycle of 20 / 10 = 2.
  The timing tool's default setup check is from launch edge 6 to C, one launch cycle; the multicycle moves it back to edge 4.
* After the setup multicycle, the timing tool checks the hold at the setup capture edge, from the next launch edge: 6 to C.
  The configured hold check, 4 to A, is the same check as 12 to C, three launch cycles later.
  The hold requirement is 0 - 20 = -20 ns, a hold multicycle of (20 - -20) / 10 - 1 = 3.

Capture on the launching edge
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A setup capture edge at the same time as the setup launch edge, a setup requirement of 0, means the edge that launches the data also captures it, after the clock's delay to the register.
It is written as a setup multicycle of 0.
For double data rate, each edge captures the data it launches, so the multicycle and false paths are written for each edge:
the setup checks move to the same edge, an edge does not capture the data the other edge launches,
and the hold check of an edge is against the data the other edge launches next.

Bidirectional ports
^^^^^^^^^^^^^^^^^^^

A port timed in both directions, such as MDIO, has an input delay and an output delay.
The timing tool joins them into a path from the port to itself through the pad, which does not exist in the design.
The report script leaves it out of the timing reports, but the timing tool still times it, and it would be the worst hold path in the design.
So the last section of the port ends with a false path from the port to itself, after the multicycle paths:

.. code-block:: tcl

   set_false_path -from [get_ports IO_MDIO] -to [get_ports IO_MDIO]

Constraints file
----------------

The constraints file is written for a reader who has to review the constraints or compare them with a timing report.
Every number in a constraint is shown with the calculation and the inputs it comes from.

:Section 1, References: The md5sum of the interface, part and traces files, and the datasheet of the part.
:Section 2, Block Diagram: The device, the part and the traces between them, with the registers of each port and their clocks (see :doc:`block_diagram`).
:Section 3, Inputs: The delay of each trace, marking default delays, and the timing of each part pin the traces reach.
:Section 4, Clocks: One section for each clock that crosses the board: generated where the device generates it, or created on the port it enters the device on.
:Section 5, Ports: One section for each port of the interface.

The section of an analyzed port starts with its edges diagram and its setup and hold requirements, with the edges they come from.
An ``SDR-SS-O-FLC`` port has two windows, each followed by its requirement (see :doc:`methodology`).
The requirements are the values to compare with the requirements in the timing reports.

Each constraint is preceded by a comment explaining its arguments, in the order they appear.
An argument is explained once, at the first constraint of the port that uses it.

The section of a deferred port says ``Deferred``.

Report script
-------------

The report script writes the setup and hold timing reports of every analyzed port, at the Slow and Fast corners, to the file the port lists in ``timing_reports``.
Run it after the design is implemented and the constraints are applied:

.. code-block:: text

   source report.tcl

The script is written for a reader, like the constraints file:

* The header names the stacv version and the command that generated the script, and under ``Requires`` the environment variables the report paths use.
* Before any corner is changed, the script checks its paths (see below).
* There is one section for each corner.
  Each section turns on its corner, turns off the other, and lists every port of the interface under its name.
* A deferred port is listed as ``Deferred``, with no reports.
* The reports of an output port are the paths through it to the clock of its output delay (``-to [get_clocks …] -through [get_ports …]``), and the reports of an input port the paths through it from the clock of its input delay (``-from [get_clocks …] -through [get_ports …]``).
  The device side is left open, so every register that drives or captures the port is reported, whatever its clock.
  Naming the delay's clock keeps out the path through a bidirectional pad, from the port to itself, which Vivado reports in place of the register paths when only one process corner is on.
* Each report asks for every path, up to 100 (``-max_paths 100 -nworst 100``), so every register that drives or captures the port is reported; stacv checks the worst path of each register.
* The first report of a port starts its file, so reports from an earlier run are not kept.
* The script ends by restoring the Vivado default, both corners on.

Report paths
^^^^^^^^^^^^

The script writes each report where ``stacv check`` looks for it.
Environment variables are left for the timing tool to read when the script runs, so the script works in any terminal or CI job that sets them.
They do not need to be set where stacv runs, and a path that starts with one is written as it is:

=============================================  ==================================================================
``timing_reports`` entry                       Path in the script
=============================================  ==================================================================
``$SCRATCH_DIR/vivado/O_DATA_timing.rpt``      ``"$env(SCRATCH_DIR)/vivado/O_DATA_timing.rpt"``
``${SCRATCH_DIR}/vivado/O_DATA_timing.rpt``    ``"$env(SCRATCH_DIR)/vivado/O_DATA_timing.rpt"``
``/reports/O_DATA_timing.rpt``                 ``"/reports/O_DATA_timing.rpt"``
``timing_reports/O_DATA_timing.rpt``           ``"<interface file directory>/timing_reports/O_DATA_timing.rpt"``
=============================================  ==================================================================

A relative path is relative to the interface file, as in ``stacv check``.
It is written from the directory stacv runs in, so the timing tool must run in the same directory.
Use an environment variable when it does not.
Every path is quoted, so paths with spaces work.

``stacv check`` accepts any number of timing reports for a port, so reports from other scripts can be used.
The report script writes one file for each port.

Path checks
^^^^^^^^^^^

Vivado does not create directories, and an environment variable that is not set, or set to the wrong directory, only shows up as an error partway through the reports.
So the script checks its paths first, and stops with an error before it changes the corners:

* **Verify Environment Variables Exist**: one check for each variable the report paths use, in the order they first appear.
  The section is left out when no path uses a variable.
* **Verify Report Directories Exist**: one check for each analyzed port, that the directory of its report exists.

.. code-block:: tcl

   ###############################################################################
   # Verify Environment Variables Exist
   ###############################################################################
   if {![info exists env(PROJ_DIR)]} {
       error "stacv: environment variable PROJ_DIR is not set"
   }

   ###############################################################################
   # Verify Report Directories Exist
   ###############################################################################
   # O_DAC_DATA
   if {![file isdirectory "$env(PROJ_DIR)/example/texas_instruments/DAC81404/timing_reports"]} {
       error "stacv: O_DAC_DATA report directory does not exist: $env(PROJ_DIR)/example/texas_instruments/DAC81404/timing_reports"
   }

When the timing tool runs on another computer than stacv, such as Vivado on Windows, set the variables in its Tcl console with forward slashes.
Tcl reads a backslash as an escape, so ``"Z:\projects"`` loses its separators:

.. code-block:: tcl

   set env(PROJ_DIR) "Z:/home/user/projects/sta-constraint-validator"

Not supported yet
^^^^^^^^^^^^^^^^^

* Buses: each port is reported as one path.

Errors
------

``stacv generate`` stops with an error, and writes no constraints, when an analyzed port:

* forwards a clock without a ``generator`` (generate_001).
* has a setup or hold requirement that is not a whole number of step periods (generate_002, generate_003).
  The capture edge does not line up with a launch edge, and the hardware cannot produce that clock.
* has a setup multicycle less than 0 (generate_004).
* has a hold multicycle less than 0 (generate_005).
* has no trace from the device to the part, or from the part to the device for an SDR-SS-RT-DI port (generate_007).
* has a trace to a pin the part does not have (generate_008).
* has no clock trace from its clock port to the clock pin of the part pin (generate_009).

``stacv generate report_tcl`` stops with an error when an analyzed port lists more than one timing report (generate_010).

Errors in the interface and traces files, such as a clock no ``[[clock]]`` table defines or an empty delay without a default, are reported when the files are read, by every command.
