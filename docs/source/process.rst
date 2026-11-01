Process
=======

.. image:: img/process.svg


Commands
--------

Each step of the process is a stacv command: a verb, then what it acts on.

.. code-block:: text

   stacv create template interface --output interface.toml
   stacv visualize edges interface.toml
   stacv generate xdc interface.toml --output interface.xdc
   stacv generate report_tcl interface.toml --output interface_stacv_report.tcl
   stacv check interface.toml

Run ``stacv`` alone to list the commands.
A command given without its arguments, or with a wrong one, prints its help and then the error, so each next word can be found from the terminal.
