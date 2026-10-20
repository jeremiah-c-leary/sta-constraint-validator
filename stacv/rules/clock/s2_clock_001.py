'''
:Stage: 2 - across timing reports
:Applies to: all
:Reads: ``launch_clock_path`` resource of every delay
:Depends on: s1_clock_001

The launch clock path must pass through the same cells and nets, in the same order, in every timing report.
Their delays are expected to differ between process corners and between setup and hold, but the route the clock takes is not.
If the route differs, the timing reports are not timing the same launch clock, and the setup and hold results cannot be compared.

**Violation**

The setup timing report clocks the source register through a global buffer, and the hold timing report through a clock manager:

.. code-block:: text
   :emphasize-lines: 5, 12-13

     Setup timing report, Slow process corner:
     ---------------------------------------------------------------------------------------------
       K18                  IBUF (Prop_ibuf_I_O)         0.968     0.968 r  I_CLK_IBUF_inst/O
                            net (fo=1, routed)           1.800     2.768    I_CLK_IBUF
       BUFGCTRL_X0Y16       BUFG (Prop_bufg_I_O)         0.096     2.864 r  I_CLK_IBUF_BUFG_inst/O
     ---------------------------------------------------------------------------------------------

     Hold timing report, Fast process corner:
     ---------------------------------------------------------------------------------------------
       K18                  IBUF (Prop_ibuf_I_O)         0.160     0.160 r  I_CLK_IBUF_inst/O
                            net (fo=1, routed)           0.411     0.571    I_CLK_IBUF
       MMCME2_ADV_X0Y0      MMCME2_ADV (Prop_mmcme2_adv_CLKIN1_CLKOUT0)
                                                         -1.201    -0.630 r  clk_wiz_inst/CLKOUT0
     ---------------------------------------------------------------------------------------------

**Result**

When the rule fails, it lists every timing report with the file and line where its launch clock path starts.
Timing reports with the same launch clock path share a label.
The labels are numbered in the order the paths first appear, so ``path 1`` is the path of the first timing report, not necessarily the correct one:

.. code-block:: text

     O_DAC_DATA_timing.rpt:32  path 1
     O_DAC_DATA_timing.rpt:98  path 1
     O_DAC_DATA_timing.rpt:176  path 2
     O_DAC_DATA_timing.rpt:242  path 1

**Likely causes**

* The timing reports were generated from different implementation runs or design checkpoints.
* The worst path at one process corner starts at a different source register, which is clocked through a different clock buffer.
* The launch clock passes through a clock mux, and the timing tool selects a different branch for setup and for hold.

Refer to the vendor's timing report documentation.
'''

from stacv.rules import path_comparisons

RULE_ID = 's2_clock_001'
FAILURE_MESSAGE = 'Launch clock path is not the same over all timing reports.'


def check(oTimingReportList):
    '''
    Purpose:  Launch clock paths pass through the same elements in every timing report.
    '''
    return path_comparisons.check_paths_match(oTimingReportList.reports, 'launch_clock_path', RULE_ID, FAILURE_MESSAGE)
