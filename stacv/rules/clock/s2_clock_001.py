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

**Likely causes**

* The timing reports were generated from different implementation runs or design checkpoints.
* The worst path at one process corner starts at a different source register, which is clocked through a different clock buffer.
* The launch clock passes through a clock mux, and the timing tool selects a different branch for setup and for hold.

Refer to the vendor's timing report documentation.
'''


def check(oTimingReportList):
    '''
    Purpose:  Launch clock paths pass through the same elements in every timing report.
    '''
    lUniqueLaunchClockPaths = extract_unique_launch_clock_paths(oTimingReportList)
    return has_at_most_one_path(lUniqueLaunchClockPaths)


def extract_unique_launch_clock_paths(oTimingReportList):
    lUniqueLaunchClockPaths = []
    for oTimingReport in oTimingReportList.reports:
        lResources = extract_path_resources(oTimingReport)
        if is_a_unique_path(lResources, lUniqueLaunchClockPaths):
            lUniqueLaunchClockPaths.append(lResources)
    return lUniqueLaunchClockPaths


def has_at_most_one_path(lUniqueLaunchClockPaths):
    return len(lUniqueLaunchClockPaths) <= 1


def extract_path_resources(oTimingReport):
    return oTimingReport.launch_clock_path.get_resources()


def is_a_unique_path(lResources, lUniqueLaunchClockPaths):
    return lResources not in lUniqueLaunchClockPaths
