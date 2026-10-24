'''
:Stage: 1 - within one timing report
:Applies to: all
:Reads: ``launch_clock_path`` first delay, ``capture_clock_path`` first delay
:Depends on: none

The launch clock path and the capture clock path must start at the same clock source.
In a forwarded clock interface, both clocks come from one input clock.
If the paths start at different points, the relationship between the clocks is not defined by the design, and clock pessimism removal has no common section to work from.

**Violation**

The launch clock path starts at ``I_CLK`` and the capture clock path starts at ``I_CLK2``:

.. code-block:: text
   :emphasize-lines: 4, 11

       ---------------------------------------------------------------------------------------
                            (clock clk_100mhz rise edge)     0.000     0.000 r
       K18                                               0.000     0.000 r  I_CLK (IN)
                            net (fo=0)                   0.000     0.000    I_CLK
       K18                  IBUF (Prop_ibuf_I_O)         0.160     0.160 r  I_CLK_IBUF_inst/O
       ---------------------------------------------------------------------------------------
                                   ...
       ---------------------------------------------------------------------------------------
                            (clock dac_sclk rise edge)     0.000     0.000 r
       L17                                               0.000     0.000 r  I_CLK2 (IN)
                            net (fo=0)                   0.000     0.000    I_CLK2
       L17                  IBUF (Prop_ibuf_I_O)         0.348     0.348 r  I_CLK2_IBUF_inst/O

**Result**

The rule checks each timing report on its own and gives one result per timing report.
When it fails, it lists the file and line where each clock path starts, with the point it starts at:

.. code-block:: text

     O_DAC_DATA_timing.rpt:32  launch clock path starts at I_CLK
     O_DAC_DATA_timing.rpt:51  capture clock path starts at I_CLK2

**Likely causes**

* The generated capture clock was created from the wrong master clock.
* The two input clocks reach the logic through a clock mux.
  The timing tool times each side through whichever branch is worst for the check.
  For setup, that is the longer branch on launch and the shorter branch on capture.

Refer to the vendor's timing constraints documentation for generated clocks and clock muxes.
'''

from stacv.results import rule_result
from stacv.rules import rule_details

RULE_ID = 's1_clock_001'
FAILURE_MESSAGE = 'Launch and capture clock do not start at the same point.'


def check(oPortProfile):
    '''
    Purpose:  Launch and capture clock paths start at the same point.
    '''

    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:

        sLaunchClockStartPoint = get_start_point(oTimingReport.launch_clock_path)
        sCaptureClockStartPoint = get_start_point(oTimingReport.capture_clock_path)
    
        if sLaunchClockStartPoint != sCaptureClockStartPoint:
            lDetails.extend(create_details(oTimingReport))

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def create_details(oTimingReport):
    lDetails = []
    lDetails.append(create_start_point_detail(oTimingReport.launch_clock_path, 'launch clock path'))
    lDetails.append(create_start_point_detail(oTimingReport.capture_clock_path, 'capture clock path'))
    return lDetails


def create_start_point_detail(oPath, sPathName):
    sStartPoint = get_start_point(oPath)
    sMessage = f'{sPathName} starts at {sStartPoint}'
    return rule_details.format_detail(oPath.first_line, sMessage)


def get_start_point(oPath):
    return oPath.delays[0].resource
