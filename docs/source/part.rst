Part
====

The part is the ???.

.. code-block:: yaml

    part:
        vendor:  <vendor_name>
        name:  <part_name>
        interface:
            - <interface_name>:
                clock:
                    - <clock_pin_name>:
                        max_freq: '20 MHz'
                data:
                    - <input_data_pin_name>:
                        setup: <setup_value>
                        hold: <hold_value>
                        type: <interface_type>
                    - <output_data_pin_name>:
                        cko_max: <clock_to_out_max>
                        cko_min: <clock_to_out_min>
                        type: <interface_type>

