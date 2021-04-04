Device
======

The device is the FPGA or ASIC which contains your design.

.. code-block:: yaml

    device:
        vendor:  <vendor_name>
        name:  <part_name>
        interface:
            - <interface_name>:
                internal_clock:
                    <internal_clock_name>:
                        frequency: <clock_frequency>
                external_clock:
                    <clock_pin_name>:
                        frequency: <clock_frequency>
                data:
                    - <output_pin_name>:
                        launch_clock: <internal_clock_name>
                        clock_edges:
                            from: <launching_clock_edge>
                            setup: <capturing_clock_edge>
                            hold: <capturing_clock_edge>
                    - <input_pin_name>:
                        capture_clock: <internal_clock_name>
                        clock_edges:
                            from: <launching_clock_edge>
                            setup: <capturing_clock_edge>
                            hold: <capturing_clock_edge>

+----------------------+----------+------------------------------------------------------------------------------+
| **Element**          | **Type** | **Description**                                                              |
+----------------------+----------+------------------------------------------------------------------------------+
| vendor_name          | string   | The manufacturer of the part.                                                |
+----------------------+----------+------------------------------------------------------------------------------+
| part_name            | string   | The name of the part.                                                        |
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
        vendor:  Intel
        name:  S10
        interface:
            - DAC_DATA_INTF:
                internal_clock:
                    internal_100mhz_int_:
                        frequency: '100 MHz'
                external_clock:
                    O_DAC_SCLK:
                        frequency: '20 MHz'
                data:
                    - O_DAC_DATA:
                        launch_clock: 'internal_100mhz_int_'
                        clock_edges:
                            from: 11
                            setup: 'c'
                            hold: 'd'
                    - I_DAC_DATA:
                        capture_clock: 'internal_100mhz_int_'
                        clock_edges:
                            from: 3
                            setup: 'f'
                            hold: 'q'
