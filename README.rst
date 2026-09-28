STA Constraint Validator
========================

A tool to work with static timing constraints.

Validating reports and CI/CD
----------------------------

``stacv report`` is a design rule check for the static timing of external
interfaces.  Where ``check_timing`` confirms constraints are complete, these
checks confirm they are correct for the interface.  Every check has a
permanent ID with a stage prefix: INT (intent consistency), COV (coverage),
STR (path structure), EDG (launch and capture edges), DLY (input and output
delays) and SLK (slack).  List them with ``bin/stacv checks``, or write the
documentation page with ``bin/stacv checks --rst docs/source/checks.rst``.
A check is skipped until the checks it depends on pass, so slack is never
judged on constraints that do not match the intent::

    bin/stacv report example/config.yaml dac_spi.setup.rpt dac_spi.hold.rpt \
        --junit results.xml

``results.xml`` is JUnit XML with one test suite per interface pin.
The command exits with status 1 when any check fails, so a pipeline stage
such as the following fails the build::

    - name: Validate timing constraints
      run: bin/stacv report timing/config.yaml build/reports/*.rpt --junit results.xml

The checks and JUnit output need only the standard library and PyYAML.
