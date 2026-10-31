Generating Constraints
======================

stacv generates the timing constraints of an interface from the same files it uses to check the timing reports.
The constraints, the visualizations and the checks all come from one interface file, so the generated constraints time the edges and delays the checks expect.

.. code-block:: text

   stacv generate xdc interface.toml
   stacv generate xdc interface.toml --output constraints.xdc

The ``xdc`` target writes a Vivado constraints file for the interface.
It is written to standard output, or to the file named by ``--output``.
An ``sdc`` target is planned for other vendors.

The intended process is:

#. Write the part and traces files.
#. Write the interface file.
#. Confirm the launch and capture edges with ``stacv visualize edges``.
#. Generate the constraints and apply them in the timing tool.
#. Run the timing reports back through ``stacv check``.

The checks confirm the timing tool applied the constraints as intended.
The DAC81404 example in ``example/texas_instruments/DAC81404`` goes through the whole process, and ``example/constraints.xdc`` is its generated constraints file.

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
``stacv generate`` stops with an error if the capture clock of an analyzed port has none.

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

* The launch clock is defined by the design, so it is not generated.
* Both clocks have a 50% duty cycle.
* The longer period is an integer multiple of the shorter period.

Clocks with other duty cycles are not supported.
They will be added if they are requested.

Constraints
-----------

Generated clock
^^^^^^^^^^^^^^^

Each capture clock is generated once, on its generator:

:Name: The name of the clock.
:Source: ``generator.source`` / ``generator.master_pin``
:Object: ``generator.source`` / ``generator.target_pin``
:Ratio: Divide by capture period / master clock period when the capture clock is slower.
        Multiply by master clock period / capture period when the capture clock is faster.

The generated clock is defined where it is generated, not on the clock port.

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
Each multicycle path applies from the launch clock to the port, so ports that share clocks can use different edges.

For example, a 10 ns launch clock and a 40 ns capture clock, with ``setup_edge = 4`` to ``"C"`` and ``hold_edge = 4`` to ``"A"``:

* The setup requirement is 40 - 20 = 20 ns, a setup multicycle of 20 / 10 = 2.
  The timing tool's default setup check is from launch edge 6 to C, one launch cycle; the multicycle moves it back to edge 4.
* After the setup multicycle, the timing tool checks the hold at the setup capture edge, from the next launch edge: 6 to C.
  The configured hold check, 4 to A, is the same check as 12 to C, three launch cycles later.
  The hold requirement is 0 - 20 = -20 ns, a hold multicycle of (20 - -20) / 10 - 1 = 3.

Constraints file
----------------

The constraints file is written for a reader who has to review the constraints or compare them with a timing report.
Every number in a constraint is shown with the calculation and the inputs it comes from.

:Section 1, References: The md5sum of the interface, part and traces files, and the datasheet of the part.
:Section 2, Block Diagram: The device, the part and the traces between them.
:Section 3, Inputs: The delay of each trace, marking default delays, and the timing of each part pin the traces reach.
:Section 4, Generated Clocks: One section for each generated clock.
:Section 5, Ports: One section for each port of the interface.

The section of an analyzed port starts with its edges diagram and its setup and hold requirements, with the edges they come from.
The requirements are the values to compare with the requirements in the timing reports.

Each constraint is preceded by a comment explaining its arguments, in the order they appear.
An argument is explained once, at the first constraint of the port that uses it.

The section of a deferred port says ``Deferred``.

Errors
------

``stacv generate`` stops with an error, and writes no constraints, when an analyzed port:

* has a capture clock without a ``generator`` (generate_001).
* has a setup or hold requirement that is not a whole number of step periods (generate_002, generate_003).
  The capture edge does not line up with a launch edge, and the hardware cannot produce that clock.
* has a setup multicycle less than 1 (generate_004).
* has a hold multicycle less than 0 (generate_005).
* has setup and hold capture edges that are not the same type, one rising and one falling (generate_006).
* has no trace from the device to the part (generate_007).
* has a trace that ends at a pin the part does not have (generate_008).
* has no clock trace from its clock port to the clock pin of the part pin (generate_009).

Errors in the interface and traces files, such as a clock no ``[[clock]]`` table defines or an empty delay without a default, are reported when the files are read, by every command.
