sta-constraint-validator (stacv)
================================

stacv writes the timing constraints of an FPGA's external interfaces, and checks that the timing tool applied them as intended.
The inputs are small text files of facts: the names in the design, the part's timing from its datasheet, and the board's trace delays.
Every constraint is derived from them, and every timing report is checked against them, the same way every time.

How an agent uses stacv
-----------------------

Timing an interface is a solved problem with many details that fail silently: a forwarded clock left out of a delay, a multicycle path on the wrong edge, a report that passes while its constraint is wrong.
An agent can reason its way through them, but it pays for that reasoning every time, and gets a different explanation each time.
stacv does the solved part, so the agent spends its tokens only on what changes from design to design:

#. **Extract the facts.**  The agent reads the HDL, the part's datasheet and the board's trace delays, and fills in three files: for SPI, ``spi_config.toml``, ``part.toml`` and ``traces.toml``.
   The one judgement in them, when the design launches and captures each signal, is written with the line of the HDL it comes from.
#. **Check them as pictures.**  ``stacv visualize edges`` and ``stacv visualize block_diagram`` show the edges and the paths, to compare with the datasheet and the design before anything is built.
#. **Generate.**  ``stacv generate xdc`` and ``stacv generate report_tcl`` write the constraints, each explained, and the script that reports their timing.
#. **Run the timing tool**, in the project's own flow.
#. **Check.**  ``stacv check`` reads the timing reports and prints PASSED, with the worst slack, or FAILED, with the rule, file and line, for each port, in milliseconds and with an exit code for CI.

``AGENTS.md``, at the root of the repository, is the page an agent reads first: the workflow, the keys to fill in, how to choose a methodology, and how to read the results.
With it and the comments in the templates, an agent timed an SPI interface it had not seen, exactly, in under three minutes.

Where people start
------------------

* :doc:`process`: the seven steps every interface goes through.
* :doc:`commands`: what each command does.
* :doc:`spi`: timing an SPI interface.
* :doc:`methodology`: how each kind of signal is timed, and why each constraint is there.

.. toctree::
   :maxdepth: 2
   :caption: Using stacv

   process
   commands

.. toctree::
   :maxdepth: 2
   :caption: Interface Patterns

   spi
   rmii

.. toctree::
   :maxdepth: 2
   :caption: Quality of results

   eye
   datasheet

.. toctree::
   :maxdepth: 2
   :caption: Checks and Errors

   check_output
   trc
   errors

.. toctree::
   :maxdepth: 2
   :caption: Methodologies

   methodology
   standards

.. toctree::
   :maxdepth: 2
   :caption: Theory of operation

   spi_config
   rmii_config
   interface
   part
   traces
   create
   generate
   block_diagram


Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
