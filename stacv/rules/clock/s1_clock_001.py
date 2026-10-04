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

**Likely causes**

* The generated capture clock was created from the wrong master clock.
* The two input clocks reach the logic through a clock mux.
  The timing tool times each side through whichever branch is worst for the check.
  For setup, that is the longer branch on launch and the shorter branch on capture.

Refer to the vendor's timing constraints documentation for generated clocks and clock muxes.
'''


def check(oTimingReport):
    '''
    Purpose:  Launch and capture clock paths start at the same point.
    '''

    sLaunchClockStartPoint = oTimingReport.launch_clock_path.delays[0].resource
    sCaptureClockStartPoint = oTimingReport.capture_clock_path.delays[0].resource

    if sLaunchClockStartPoint != sCaptureClockStartPoint:
        return False
    return True
