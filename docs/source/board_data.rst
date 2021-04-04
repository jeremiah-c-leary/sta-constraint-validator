Board Data
==========

The board data data structure contains all the information about trace delays.
It has the following basic structure:

.. code-block:: yaml

    board:
        trace:
            - <trace_name>:
                device_pin: <pin_name>
                part_pin: <pin_name>
                delay:
                    max: <max_delay>
                    min: <min_delay>

+-------------+----------+---------------------------------------------------------------------+
| **Element** | **Type** | **Description**                                                     |
+-------------+----------+---------------------------------------------------------------------+
| trace_name  | string   | The name of the trace on the board.                                 |
+-------------+----------+---------------------------------------------------------------------+
| pin_name    | string   | Name of the pin on the device or part the trace connects to.        |
+-------------+----------+---------------------------------------------------------------------+
| max_delay   | float    | The maximum delay of the trace.                                     |
+-------------+----------+---------------------------------------------------------------------+
| min_delay   | float    | The minimum delay of the trace.                                     |
+-------------+----------+---------------------------------------------------------------------+

Example
-------

The following example will illustrate how to fill out the data structure.

.. image:: board_data.svg

The above image would result in the following YAML file:

.. code-block:: yaml

    board:
        trace:
            - read_data:
                device_pin: 'E'
                part_pin: 'F'
                delay:
                    max: 1.0
                    min: 0.5
            - write_data:
                device_pin: 'C'
                part_pin: 'D'
                delay:
                    max: 1.0
                    min: 0.5
            - clock:
                device_pin: 'A'
                part_pin : 'B'
                delay:
                    max: 1.0
                    min: 0.5
