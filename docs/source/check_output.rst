Check Output
============

``stacv check`` reads the timing reports of every port and checks them against the input files (see :doc:`trc` for the rules).
It prints a result for each port, and can write a report file and a JUnit file.

The console
-----------

It prints the files it reads, and a result for every port of the interface, in the order of the ports:

.. code-block:: text

   Reading interface file interface.toml
   Reading timing report file timing_reports/O_DAC_DATA_timing.rpt
   PASSED: O_DAC_DATA.SDR-SS-O  setup slack 7.311 ns, hold slack 7.092 ns
   Reading timing report file timing_reports/O_DAC_SDEN_F_timing.rpt
   FAILED: [s5_slack_001] O_DAC_SDEN_F.SDR-SS-O-FLC
       timing_reports/O_DAC_SDEN_F_timing.rpt:14  setup slack -10.295ns
   DEFERRED: O_DAC_LDAC

* ``PASSED:`` every rule of the port passed, followed by the worst setup and hold slack of all the port's paths, in every corner its reports give.
  A failed port's slack is not shown, as a failing rule can mean the timing tool's slack is wrong.
* ``FAILED:`` one line for each failing rule, followed by its details, each indented four spaces with the file and line it comes from.
  Rules skipped because an earlier stage failed are not printed.
* ``DEFERRED:`` the port has ``status = "defer"``, or its methodology has no rules yet, and is not checked; its timing reports are not read.

Each result names the port as ``<port>.<methodology>``, the same identifier as in the report and JUnit files, so it can be searched for in a CI log.
Paths are shown relative to where stacv runs; the report file keeps them in full.
When every port passes, the last line is ``Check Passed``.

stacv exits with code 0 when every port passes, 1 when a rule fails, and 2 on an input error (see :doc:`errors`).

The report file
---------------

``--report <file>`` writes a report with three sections:

#. **Summary**: the interface, and a row for each port with its result and, for a passed port, its worst setup and hold slack.
#. **Inputs**: the md5sum of the interface file and of every timing report, so the report says exactly what it checked.
#. **Port Rule Checks**: for each analyzed port, the result of every rule, stage by stage, with the details of each failure.

.. code-block:: text

   Port        Methodology    Report Key               Section   Result   Setup Slack   Hold Slack
   ---------   ------------   ----------------------   -------   ------   -----------   ----------
   dac_sdi     SDR-SS-O       dac_sdi.SDR-SS-O         3.1       Passed   32.553 ns     35.154 ns
   dac_scs_n   SDR-SS-O-FLC   dac_scs_n.SDR-SS-O-FLC   3.2       Passed   35.538 ns     74.670 ns
   dac_sdo     SDR-SS-RT-DI   dac_sdo.SDR-SS-RT-DI     3.3       Passed   20.949 ns     43.099 ns

A failed or deferred port shows ``-`` for its slack.

The JUnit file
--------------

``--junit <file>`` writes a JUnit file, which CI systems read to show and count results: one testsuite for each port, named ``<port>.<methodology>``, and one testcase for each rule.
A failing rule is a failure in its testcase, and names the timing report file and line.

.. code-block:: xml

   <testsuites name="stacv" tests="72" failures="0" skipped="0">
     <testsuite name="dac_sdi.SDR-SS-O" tests="24" failures="0" skipped="0">
       <testcase name="s0_timing_report_001" classname="dac_sdi.SDR-SS-O" />
       ...
