'''
:Stage: 0 - inputs
:Applies to: SDR-SS-RT
:Reads: first element of the data path of every timing report, ``name`` of the port in the configuration
:Depends on: none

The data path of every timing report of a port must start at the port.
Every timing report is checked, setup and hold, at every process corner.
In a round trip, the data path starts where the data enters the device: the input delay, then the net from the port, which the timing tool names after the port.
If the data path starts anywhere else, the timing report times a different port or an internal path, and the results of the other rules do not apply to the port.

**Violation**

The port is configured with ``name = "I_DAC_SDO"``, but the data path of the timing report starts at ``I_DAC_DATA``:

.. code-block:: text
   :emphasize-lines: 3

                            input delay                 34.000    42.200
       W16                                               0.000    42.200 r  I_DAC_DATA (IN)
                            net (fo=0)                   0.000    42.200    I_DAC_DATA
       W16                  IBUF (Prop_ibuf_I_O)         0.864    43.065 r  I_DAC_DATA_IBUF_inst/O

**Result**

When the rule fails, it lists each timing report whose data path starts somewhere else, with the file and line of the first element of the data path:

.. code-block:: text

     I_DAC_DATA_timing.rpt:52  data path starts at I_DAC_DATA, configured port I_DAC_SDO

**Likely causes**

* The wrong timing report is listed under the port.
* The port name in the configuration is wrong.
* The timing report was generated for every path captured by a clock, rather than for paths from the port, and the worst path is internal.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's0_data_path_002'
FAILURE_MESSAGE = 'Data path in timing reports does not start at the configured port.'


def check(oPortProfile):
    '''
    Purpose:  Compares the first element of the data path in the timing reports to the configured port.
    '''
    lDetails = get_data_path_start_mismatches(oPortProfile)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_data_path_start_mismatches(oPortProfile):
    sPortName = oPortProfile.port.name
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        oDataPathStart = oTimingReport.data_path.get_first_delay()
        if oDataPathStart.resource != sPortName:
            sErrorMessage = generate_error_message(oDataPathStart, sPortName)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oDataPathStart, sPortName):
    sMessage = f'data path starts at {oDataPathStart.resource}, configured port {sPortName}'
    return rule_details.format_detail(oDataPathStart.line, sMessage)
