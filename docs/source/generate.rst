Generating Constraints
======================

stacv generates the timing constraints of an interface from the same files it uses to check the timing reports.
The constraints, the visualizations and the checks all come from one interface file, so the generated constraints time the edges and delays the checks expect.

.. code-block:: text

   stacv generate xdc interface.toml

The ``xdc`` target writes Vivado constraints for every port in the interface file to standard output.
An ``sdc`` target is planned for other vendors.

The intended process is:

#. Write the part and traces files.
#. Write the interface file.
#. Confirm the launch and capture edges with ``stacv visualize edges``.
#. Generate the constraints and apply them in the timing tool.
#. Run the timing reports back through ``stacv check``.

The checks confirm the timing tool applied the constraints as intended.

Applies to
----------

SDR-SS-O.
Other methodologies are added as they are supported by the checks.

Interface file
--------------

Generating constraints needs one key that the checks do not use, ``source`` in the capture clock:

.. code-block:: toml

   capture_clock = {port = "O_DAC_SCLK", name = "dac_sclk", period = 40.000, generator = {source = "q_spi_output_clock_reg", master_pin = "C", target_pin = "Q"}, setup_edge = "C", hold_edge = "A"}

``generator`` is a dictionary that names the source of the generated clock and the pins associated with it.
It is the register that forwards the clock, a clock manager, or anything else that drives the clock port.
It also tells a reviewer where the forwarded clock comes from.

``generator`` is optional for ``stacv check`` and ``stacv visualize``.
``stacv generate`` stops with an error if it is missing.

Assumptions
-----------

* The launch clock is defined by the design, so it is not generated.
* The clock at the ``source`` pin is the launch clock.
* Both clocks have a 50% duty cycle.
* The longer period is an integer multiple of the shorter period.

Clocks with other duty cycles are not supported.
They will be added if they are requested.

Constraints
-----------

Generated clock
^^^^^^^^^^^^^^^

The generated capture clock is created based on the "generated" key.

:Name: ``capture_clock.name``
:Clock port: ``capture_clock.port``
:Source: ``capture_clock.source``
:Ratio: Divide by capture period / launch period when the capture clock is slower.
        Multiply by launch period / capture period when the capture clock is faster.

A capture clock shared by several ports is generated once.

Output delays
^^^^^^^^^^^^^

Each port gets a maximum and a minimum output delay against the capture clock.
They are the values the stage 3 rules check:

:Maximum: part setup + data trace maximum delay - clock trace minimum delay
:Minimum: \- part hold + data trace minimum delay - clock trace maximum delay

When the capture edges are falling edges (B, D, F, ...), the output delays are applied to the falling edge of the capture clock.

Multicycle paths
^^^^^^^^^^^^^^^^

The timing tool times the closest pair of launch and capture edges by default.
Multicycle paths move the setup and hold checks to the configured edges.
They are counted in cycles of the faster clock, the step clock:

* When the launch clock is faster, the multicycle paths move the launch edge.
* Otherwise, they move the capture edge.

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
* After the setup multicycle, the timing tool checks the hold at the same edge as the setup launch edge from launch edge 6 to C.
  The configured hold check, 4 to A, is the same check as 12 to C, three launch cycles later.
  The hold requirement is 0 - 20 = -20 ns, a hold multicycle of (20 - -20) / 10 - 1 = 3.

Errors
------

``stacv generate`` stops with an error, and writes no constraints, when:

* ``source`` is missing from a capture clock.
* A setup or hold requirement is not a whole number of step periods.
  The capture edge does not line up with a launch edge, and the hardware cannot produce that clock.
* The setup multicycle is less than 1.
* The hold multicycle is less than 0.
* The setup and hold capture edges are not the same type, one rising and one falling.
