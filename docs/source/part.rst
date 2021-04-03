Part
====

The part is the external device the FPGA/ASIC is communicating with.
It is typically provided by a vendor. 

.. code-block:: yaml

    part:
        vendor:  <vendor_name>
        name:  <part_name>
        interface:
            - <interface_name>:
                timing_model : <interface_type>
                clock:
                    - <clock_pin_name>:
                        max_freq: '20 MHz'
                data:
                    - <input_pin_name>:
                        <clock_edge>:
                            setup: <setup_value>
                            hold: <hold_value>
                    - <output_pin_name>:
                        <clock_edge>:
                            clock_to_out:
                                max: <clock_to_out_max>
                                min: <clock_to_out_min>

+------------------+----------+------------------------------------------------------------------------------+
| **Element**      | **Type** | **Description**                                                              |
+------------------+----------+------------------------------------------------------------------------------+
| vendor_name      | string   | The manufacturer of the part.                                                |
+------------------+----------+------------------------------------------------------------------------------+
| part_name        | string   | The name of the part.                                                        |
+------------------+----------+------------------------------------------------------------------------------+
| interface_name   | string   | Parts can have multiple interfaces.  Each must be uniquely identified.       |
+------------------+----------+------------------------------------------------------------------------------+
| timing_model     | string   | The type of timing required for this interface.                              |
+------------------+----------+------------------------------------------------------------------------------+
| clock_pin_name   | string   | The clock pin the data pins are referenced to.                               |
+------------------+----------+------------------------------------------------------------------------------+
| input_pin_name   | string   | Each input pin will have an entry.                                           |
+------------------+----------+------------------------------------------------------------------------------+
| clock_edge       | string   | The edge the setup, hold or clock to out applies to.  "rising" or "falling"  |
+------------------+----------+------------------------------------------------------------------------------+
| setup_value      | float    | The setup requirement for the input pin.                                     |
+------------------+----------+------------------------------------------------------------------------------+
| hold_value       | float    | The hold requirement for the input pin.                                      |
+------------------+----------+------------------------------------------------------------------------------+
| output_pin_name  | string   | Each output pin will have an entry.                                          |
+------------------+----------+------------------------------------------------------------------------------+
| clock_to_out_max | float    | The maximum delay of the pin relavite to the clock pin.                      |
+------------------+----------+------------------------------------------------------------------------------+
| clock_to_out_min | float    | The minimum delay of the pin relavite to the clock pin.                      |
+------------------+----------+------------------------------------------------------------------------------+

Example
-------

The following example uses a Texas Instruments DAC81404 part.

.. code-block:: yaml

    part:
        vendor:  Texas Instruments
        name:  DAC81404
        interface:
            - serial_interface:
                timing_model : 'ource synchronous with round trip'
                clock:
                    - SCLK:
                        max_freq: '50 MHz'
                data:
                    - SDIN:
                        falling_edge:
                            setup:
                                id: 'tSDIS'
                                value: '5 ns'
                            hold:
                                id: 'tSDIH'
                                value: '5 ns'
                    - SYNC_F:
                        falling_edge:
                            setup:
                                id: 'tCSS'
                                value: '20 ns'
                            hold:
                                id: 'tCSH'
                                value: '5 ns'
                    - SDO:
                        rising_edge:
                            clock_to_out:
                                name:  'tSDODLY'
                                max: '20 ns'
                                min: '0 ns'

