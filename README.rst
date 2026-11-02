STA Constraint Validator
========================

stacv writes and checks the static timing constraints of the external interfaces of an FPGA.

An interface is described in three reasonably sized TOML files, each written by the person who knows its contents:

* the part file: the part's pins, their methodologies, and the setup and hold from its datasheet
* the traces file: the board traces between the device and the part, and their delays
* the interface file: the clocks, and each port with its launch and capture edges

From these, stacv generates the constraints and the timing tool script, so nothing is calculated or typed by hand.
It then checks the timing reports against the same three files, and fails when the timing tool timed something other than what was intended: the wrong edges, the wrong output delays, the wrong clocks, or negative slack.

Commands
--------

.. code-block:: text

   stacv create template interface --output interface.toml
   stacv visualize edges interface.toml
   stacv generate xdc interface.toml --output interface.xdc
   stacv generate report_tcl interface.toml --output interface_stacv_report.tcl
   stacv check interface.toml --report stacv_report.txt --junit stacv_junit.xml

#. ``create template`` writes a starting interface, traces or part file.
#. ``visualize edges`` draws the launch and capture edges of each port, to compare with the datasheet before anything is generated.
#. ``generate xdc`` writes the constraints: generated clocks, output delays and multicycle paths, each with the calculation it comes from.
#. ``generate report_tcl`` writes the Vivado script that reports the timing paths ``check`` reads.
#. ``check`` checks the timing reports, port by port.
   It exits with 0 when every port passes, 1 when a rule fails and 2 on an input error, so it can fail a CI pipeline.
   ``--report`` writes a report file with the md5sum of every input, to keep as a record, and ``--junit`` writes a JUnit file.

stacv needs Python 3.11 and only the standard library.
Install it from a clone, which adds the ``stacv`` command:

.. code-block:: text

   python3.11 -m pip install .

Or run it from the clone without installing, with ``bin/stacv`` or ``python3.11 -m stacv``.

Example
-------

``example/texas_instruments/DAC81404`` is a DAC81404 serial interface on a Xilinx Artix-7, run through Vivado 2020.2:

* ``interface.toml``, ``traces.toml`` and ``part.toml`` describe the interface.
* ``example/constraints.xdc`` and ``example/dac_spi_1_stacv_report.tcl`` are generated from them.
* ``timing_reports`` holds the Vivado reports of those constraints, which ``stacv check`` passes.

.. code-block:: text

   $ export PROJ_DIR=$PWD
   $ bin/stacv check example/texas_instruments/DAC81404/interface.toml
   Reading interface file example/texas_instruments/DAC81404/interface.toml
   Reading timing report file example/texas_instruments/DAC81404/timing_reports/O_DAC_DATA_timing.rpt
   PASSED: O_DAC_DATA.SDR-SS-O
   Reading timing report file example/texas_instruments/DAC81404/timing_reports/O_DAC_SDEN_F_timing.rpt
   PASSED: O_DAC_SDEN_F.SDR-SS-O-FLC
   Reading timing report file example/texas_instruments/DAC81404/timing_reports/I_DAC_DATA_timing.rpt
   PASSED: I_DAC_DATA.SDR-SS-RT-DI
   Check Passed

Documentation
-------------

The documentation is in ``docs/source``:

* ``process.rst``: the commands and the check output
* ``methodology.rst``: the methodologies stacv supports, and what is not supported yet
* ``interface.rst``, ``traces.rst`` and ``part.rst``: the three input files
* ``generate.rst``: the constraints file and the report script
* ``trc.rst``: the rules ``check`` runs
* ``errors.rst``: every error message, and how to correct it

Development
-----------

Every commit must pass ``bin/gate``: the unit tests, and the documentation build with no warnings.
The build runs Sphinx from a virtual environment in ``.venv``:

.. code-block:: text

   python3.11 -m venv .venv
   .venv/bin/pip install sphinx
   bin/gate
