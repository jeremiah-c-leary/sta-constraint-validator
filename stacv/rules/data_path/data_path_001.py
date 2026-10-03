'''
:Stage: 1 - within one timing report
:Applies to: output interface
:Reads: ``destination_is_output_port``
:Depends on: none

The data path of an output interface must end at a device output port.
If it ends anywhere else, the report is timing an internal path, and the interface rules would be checking the wrong path.

**Violation**

The destination is an internal register, not an output port:

.. code-block:: text
   :emphasize-lines: 2

     Destination:            q_dac_capture_reg/D
                               (rising edge-triggered cell FDCE clocked by dac_sclk  {rise@0.000ns fall@25.000ns period=50.000ns})

**Likely causes**

* The report was generated for every path captured by a clock, rather than for paths to the interface port, and the worst path is internal.

Refer to the vendor's timing report documentation.
'''
