'''
:Stage: 0 - inputs
:Applies to: SDR-SS-O
:Reads: last element of the data path of every timing report, ``name`` of the port in the configuration
:Depends on: none

The data path of every timing report of a port must end at the port.
Every timing report is checked, setup and hold, at every process corner.
The last element of the data path is the net to the port, which the timing tool names after the port.
If the data path ends anywhere else, the timing report times a different port or an internal path, and the results of the other rules do not apply to the port.

**Violation**

The port is configured with ``name = "O_DAC_CSF"``, but the data path of the timing report ends at ``O_DAC_DATA``:

.. code-block:: text
   :emphasize-lines: 1

                            net (fo=0)                   0.000     2.986    O_DAC_DATA
       U16                                                               r  O_DAC_DATA (OUT)

**Result**

When the rule fails, it lists each timing report whose data path ends somewhere else, with the file and line of the last element of the data path:

.. code-block:: text

     O_DAC_DATA_timing.rpt:47  data path ends at O_DAC_DATA, configured port O_DAC_CSF

**Likely causes**

* The wrong timing report is listed under the port.
* The port name in the configuration is wrong.
* The timing report was generated for every path captured by a clock, rather than for paths through the port, and the worst path is internal.
'''

from stacv.results import rule_result
from stacv.rules import rule_details


RULE_ID = 's0_data_path_001'
FAILURE_MESSAGE = 'Data path in timing reports does not end at the configured port.'


def check(oPortProfile):
    '''
    Purpose:  Compares the last element of the data path in the timing reports to the configured port.
    '''
    lDetails = get_data_path_end_mismatches(oPortProfile)

    return rule_result.generate_rule_result(RULE_ID, lDetails, FAILURE_MESSAGE)


def get_data_path_end_mismatches(oPortProfile):
    sPortName = oPortProfile.port.name
    lDetails = []
    for oTimingReport in oPortProfile.timing_reports.reports:
        oDataPathEnd = oTimingReport.data_path.get_last_delay()
        if oDataPathEnd.resource != sPortName:
            sErrorMessage = generate_error_message(oDataPathEnd, sPortName)
            lDetails.append(sErrorMessage)
    return lDetails


def generate_error_message(oDataPathEnd, sPortName):
    sMessage = f'data path ends at {oDataPathEnd.resource}, configured port {sPortName}'
    return rule_details.format_detail(oDataPathEnd.line, sMessage)
