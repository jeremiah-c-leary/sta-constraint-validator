'''
:Stage: 2 - across timing reports
:Applies to: all
:Reads: ``capture_clock_path`` resource of every delay
:Depends on: s1_clock_001

The capture clock path must pass through the same cells and nets, in the same order, in every timing report.
Their delays are expected to differ between process corners and between setup and hold, but the route the clock takes is not.
In a source synchronous output, the capture clock path is the forwarded clock: from the clock input, through the clock forwarding logic, to the clock output port.
If the route differs, the timing reports are not timing the same forwarded clock, and the setup and hold results cannot be compared.

**Violation**

The setup timing report forwards the clock through a register, and the hold timing report through an output DDR register:

.. code-block:: text
   :emphasize-lines: 5, 12

     Setup timing report, Slow process corner:
     ---------------------------------------------------------------------------------------------
       BUFGCTRL_X0Y0        BUFG (Prop_bufg_I_O)         0.081     2.631 r  I_CLK_IBUF_BUFG_inst/O
                            net (fo=13, routed)          1.432     4.062    I_CLK_IBUF_BUFG
       SLICE_X0Y5           FDCE (Prop_fdce_C_Q)         0.379     4.441 r  q_spi_output_clock_reg/Q
     ---------------------------------------------------------------------------------------------

     Hold timing report, Fast process corner:
     ---------------------------------------------------------------------------------------------
       BUFGCTRL_X0Y0        BUFG (Prop_bufg_I_O)         0.026     0.817 r  I_CLK_IBUF_BUFG_inst/O
                            net (fo=13, routed)          0.591     1.408    I_CLK_IBUF_BUFG
       OLOGIC_X0Y12         ODDR (Prop_oddr_C_Q)         0.177     1.585 r  clk_forward_oddr/Q
     ---------------------------------------------------------------------------------------------

**Likely causes**

* The timing reports were generated from different implementation runs or design checkpoints.
* The clock forwarding logic was replicated, and the timing reports time different copies.
* The capture clock passes through a clock mux, and the timing tool selects a different branch for setup and for hold.

Refer to the vendor's timing report documentation.
'''

from stacv.rules import path_comparisons


def check(oTimingReportList):
    '''
    Purpose:  Capture clock paths pass through the same elements in every timing report.
    '''
    return path_comparisons.at_most_one_unique_delay_path_exists(oTimingReportList, 'capture_clock_path')
