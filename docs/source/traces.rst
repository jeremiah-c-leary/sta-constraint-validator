Traces File
===========

The traces file describes the board traces between the device and the part, and their delays.
The interface file names it with its ``traces`` key.

.. code-block:: text

   stacv create template traces --output traces.toml

Delays are in nanoseconds.
A key stacv does not read is an error (traces_config_004); see :doc:`errors` for every error.

Default delay
-------------

.. code-block:: toml

   default_delay = {max_delay = 1.00, min_delay = 0.00}

``default_delay`` is optional.
It gives the delays of every trace direction written as ``{}``, for traces whose delays are not known yet.
Delays taken from it are marked as default delays in the constraints file, so they are not mistaken for measured delays.

Traces
------

Each trace has a ``[[trace]]`` table.

.. code-block:: toml

   # A device data output:  the device writes, the part reads.
   [[trace]]
   name = "data_output"
   device_pin = "O_DATA"
   part_pin = "DATA_IN"
   device_to_part = {max_delay = 3.00, min_delay = 1.00}

   # A device data input:  the part writes, the device reads.
   [[trace]]
   name = "data_input"
   device_pin = "I_DATA"
   part_pin = "DATA_OUT"
   part_to_device = {max_delay = 3.00, min_delay = 1.00}

   # A trace that uses the default delay.
   [[trace]]
   name = "chip_select"
   device_pin = "O_CS"
   part_pin = "CS"
   device_to_part = {}

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Key
     - Required
     - Description
   * - ``name``
     - Yes
     - The unique name of the trace.
   * - ``device_pin``
     - Yes
     - The device port the trace connects to: a port name in the interface file, or the ``port`` of a clock.
   * - ``part_pin``
     - Yes
     - The part pin the trace connects to: the name of a pin, or of a clock pin, in the part file.
   * - ``device_to_part``
     - See below
     - The delays of the trace from the device to the part.
   * - ``part_to_device``
     - See below
     - The delays of the trace from the part to the device.

A trace gives one direction, or both for a pin the device and the part both drive.
Each direction is one of:

* ``{max_delay = ..., min_delay = ...}``: the maximum and minimum delays of the trace.
* ``{}``: use ``default_delay``.
  It is an error if there is no ``default_delay`` (traces_config_005).

Giving only one of ``max_delay`` and ``min_delay`` is an error (traces_config_006), and so is a ``max_delay`` less than its ``min_delay`` (traces_config_008).
A trace with neither direction is an error (traces_config_007), and each trace name is used once (traces_config_009).
