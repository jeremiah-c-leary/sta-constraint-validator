Checks
======

Every check has a permanent identifier. Numbers are never reused or renumbered.
A check is skipped until the checks it depends on pass.

Intent consistency (INT)
------------------------

INT-001: Each device data pin connects to a part pin through a board trace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The board section must contain a trace from the device data pin, and from the pin's interface clock, to pins that exist in the part section. Without these the input and output delays cannot be derived.

* Depends on: none

INT-002: Each clock referenced by a pin is defined with a frequency
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The launch and capture clocks named for the pin must be defined in the device section with a frequency, so the numbered and lettered edges can be resolved to times and matched to the clocks in the timing report.

* Depends on: none

INT-003: Device capture edge direction agrees with the part datasheet
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The device and part intent files are compared with each other: the clock edge direction the device intent uses at the part must be the edge the part datasheet specifies. This does not judge which file is correct, only that they disagree.

* Depends on: INT-001

Coverage (COV)
--------------

COV-001: Setup and hold reports present for each pin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

At least one setup (max) and one hold (min) path must be reported for the pin. Every later check is based on these paths.

* Depends on: INT-001, INT-002

COV-002: Required process corners reported
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Setup and hold paths must be reported at every required process corner (by default the slow and fast corners). Slack at one corner says nothing about the others.

* DID paragraph: 3.x.3.1 h
* Depends on: COV-001

Path structure (STR)
--------------------

STR-001: Data and clock paths share a common source
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The clock path that launches the data and the clock path that captures it must start from the same clock source. Otherwise the relationship between them is not defined by the design and the analysis is not meaningful.

* DID paragraph: 3.x.3.1 a
* Depends on: COV-001

STR-002: Clock path traces to the external clock pin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For forwarded clocks the capture clock path must reach the device pin of the interface clock. A capture clock defined elsewhere means the report is not timing the clock the part actually receives.

* DID paragraph: 3.x.3.1 c
* Depends on: COV-001

STR-003: Data path traces to the external data pin
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The data path must end at (for outputs) or start from (for inputs) the device data pin.

* DID paragraph: 3.x.3.1 d
* Depends on: COV-001

STR-004: Clock paths are the same for setup and hold
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The setup and hold analyses must use the same physical clock paths, only with different delays. Different routes indicate the two checks are timing different clock relationships.

* DID paragraph: 3.x.3.1 g
* Depends on: STR-002

STR-005: CRPR taken at the common point of the clock paths
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Clock pessimism removal must equal the delay difference of the clock path elements the launch and capture paths share, up to the point where they diverge. A different value means pessimism is removed from the wrong point.

* DID paragraph: 3.x.3.1 b
* Depends on: STR-001

Launch and capture edges (EDG)
------------------------------

EDG-001: Setup check uses the intended launch and capture edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The launch and capture edges of the setup check, and their directions, must match the numbered launch edge and lettered setup capture edge in the device intent.

* DID paragraph: 3.x.3.1 f
* Depends on: COV-001

EDG-002: Hold check uses the intended launch and capture edges
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The launch and capture edges of the hold check, and their directions, must match the numbered launch edge and lettered hold capture edge in the device intent.

* DID paragraph: 3.x.3.1 f
* Depends on: COV-001

Input and output delays (DLY)
-----------------------------

DLY-001: Max input/output delay matches datasheet and board
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The max output or input delay used by the setup check must equal the value derived from the part datasheet parameters and the board trace delays.

* DID paragraph: 3.x.3.1 e
* Depends on: COV-001, INT-001

DLY-002: Min input/output delay matches datasheet and board
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The min output or input delay used by the hold check must equal the value derived from the part datasheet parameters and the board trace delays.

* DID paragraph: 3.x.3.1 e
* Depends on: COV-001, INT-001

Slack (SLK)
-----------

SLK-001: Setup slack is positive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Worst setup slack across all reported corners must be zero or positive. Only judged once the corners, path structure, edges and max delay are confirmed.

* DID paragraph: 3.x.4 b
* Depends on: COV-002, STR-001, STR-002, STR-003, STR-004, STR-005, EDG-001, DLY-001

SLK-002: Hold slack is positive
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Worst hold slack across all reported corners must be zero or positive. Only judged once the corners, path structure, edges and min delay are confirmed.

* DID paragraph: 3.x.4 b
* Depends on: COV-002, STR-001, STR-002, STR-003, STR-004, STR-005, EDG-002, DLY-002
