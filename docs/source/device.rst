Device
======

The device is the FPGA or ASIC which contains your design.

.. code-block:: yaml

    device:
        vendor:  <vendor_name>
        name:  <part_name>
        process_corners:
            - <process_corner_name>
        interface:
            - <interface_name>:
                clock: 
                    internal:
                        -  <internal_clock_name>:
                            frequency: <clock_frequency>
                    input:
                         - <clock_pin_name>
                             frequency: <clock_frequency>
                    output:
                         - <clock_pin_name>
                             frequency: <clock_frequency>
                data:
                    output:
                         - <output_pin_name>:
                             launch_clock:
                                 name: <launching_clock_name>
                                 edge: <launching_clock_edge>
                             capture_clock:
                                 name: <capturing_clock_name
                                 edge:
                                     setup: <capturing_clock_edge>
                                     hold: <capturing_clock_edge>
                    input:
                         - <input_pin_name>:
                             launch_clock:
                                 name: <launching_clock_name>
                                 edge: <launching_clock_edge>
                             capture_clock:
                                 name: <capturing_clock_name
                                 edge:
                                     setup: <capturing_clock_edge>
                                     hold: <capturing_clock_edge>

+----------------------+----------+------------------------------------------------------------------------------+
| **Element**          | **Type** | **Description**                                                              |
+----------------------+----------+------------------------------------------------------------------------------+
| vendor_name          | string   | The manufacturer of the part.                                                |
+----------------------+----------+------------------------------------------------------------------------------+
| part_name            | string   | The name of the part.                                                        |
+----------------------+----------+------------------------------------------------------------------------------+
| process_corner_name  | string   | A process corner the timing reports must cover, named as in the reports.     |
+----------------------+----------+------------------------------------------------------------------------------+
| interface_name       | string   | Devices can have multiple interfaces.  Each must be uniquely identified.     |
+----------------------+----------+------------------------------------------------------------------------------+
| internal_clock_name  | string   | The internal clock name being used to launch or capture data.                |
+----------------------+----------+------------------------------------------------------------------------------+
| clock_frequency      | string   | The frequency of the clock.                                                  |
+----------------------+----------+------------------------------------------------------------------------------+
| clock_pin_name       | string   | The clock pin the data pins are referenced to.                               |
+----------------------+----------+------------------------------------------------------------------------------+
| output_pin_name      | string   | Each output pin will have an entry.                                          |
+----------------------+----------+------------------------------------------------------------------------------+
| launching_clock_edge | integer  | The clock edge which is launching data.                                      |
+----------------------+----------+------------------------------------------------------------------------------+
| capturing_clock_edge | integer  | The clock edge which is capturing data.                                      |
+----------------------+----------+------------------------------------------------------------------------------+
| clock_to_out_min     | float    | The minimum delay of the pin relavite to the clock pin.                      |
+----------------------+----------+------------------------------------------------------------------------------+
| input_pin_name       | string   | Each input pin will have an entry.                                           |
+----------------------+----------+------------------------------------------------------------------------------+

Example
-------

The following example assumes using the serial interface of the DAC81404 part.

.. code-block:: yaml

    part:
        vendor:  AMD
        name:  ZU19EG
        process_corners:
            - Slow
            - Fast
        interface:
            - DAC_DATA_INTF:
                clock:
                    internal:
                        internal_100mhz:
                            frequency: '100 MHz'
                    output:
                        O_DAC_SCLK:
                            frequency: '20 MHz'
                data:
                    output:
                        - O_DAC_DATA:
                            launch_clock:
                                name: 'internal_100mhz'
                                edge: 11
                            capture_clock:
                                name: 'O_DAC_SCLK'
                                edge:
                                    setup: 'c'
                                    hold: 'd'
                    input:
                        - I_DAC_DATA:
                            launch_clock:
                                name: 'O_DAC_SCLK'
                                edge: 3
                            capture_clock:
                                name: 'internal_100mhz'
                                edge:
                                    setup: 'f'
                                    hold: 'q'
