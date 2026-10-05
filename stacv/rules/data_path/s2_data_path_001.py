'''
:Stage: 2 - across timing reports
:Applies to: all
:Reads: ``data_path`` resource of every delay
:Depends on: none

The data path must pass through the same cells and nets, in the same order, in every timing report.
Their delays are expected to differ between process corners and between setup and hold, but the route the data takes is not.
If the route differs, the timing reports are timing different paths to the port, and the setup and hold results cannot be compared.

**Violation**

The setup timing report starts at the output data register, and the hold timing report starts at a different register that drives the port through the same logic:

.. code-block:: text
   :emphasize-lines: 3-4, 10-11

     Setup timing report, Slow process corner:
     ---------------------------------------------------------------------------------------------
       SLICE_X0Y3           FDCE (Prop_fdce_C_Q)         0.304     4.034 r  q_spi_output_data_reg/Q
                            net (fo=1, routed)           0.611     4.645    q_spi_output_data
       SLICE_X0Y3           LUT3 (Prop_lut3_I0_O)        0.124     4.769 r  O_DAC_DATA_OBUF_inst_i_1/O
     ---------------------------------------------------------------------------------------------

     Hold timing report, Fast process corner:
     ---------------------------------------------------------------------------------------------
       SLICE_X1Y4           FDRE (Prop_fdre_C_Q)         0.141     1.549 r  q_spi_idle_data_reg/Q
                            net (fo=1, routed)           0.210     1.759    q_spi_idle_data
       SLICE_X0Y3           LUT3 (Prop_lut3_I1_O)        0.045     1.804 r  O_DAC_DATA_OBUF_inst_i_1/O
     ---------------------------------------------------------------------------------------------

**Likely causes**

* More than one register drives the output port through logic, and the worst path at each process corner starts at a different register.
* The timing reports were generated from different implementation runs or design checkpoints.

Refer to the vendor's timing report documentation.
'''

from stacv.rules import path_comparisons


def check(oTimingReportList):
    '''
    Purpose:  Data paths pass through the same elements in every timing report.
    '''

    return path_comparisons.at_most_one_unique_delay_path_exists(oTimingReportList, 'data_path')
