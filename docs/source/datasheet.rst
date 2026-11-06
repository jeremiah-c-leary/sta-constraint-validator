Datasheet
=========

``stacv generate datasheet`` writes the datasheet of an interface: the timing of each port at the device's pins, for whoever connects a part to the device.
It is written from the timing reports, so it is generated after timing.
Its values rely on the checks, so generate it once ``stacv check`` passes the timing reports.

.. code-block:: text

   stacv generate datasheet interface.toml
   stacv generate datasheet interface.toml --output datasheet.toml

The datasheet is written to standard output, or to the file named by ``--output``.
The DAC81404 example's datasheet is ``example/texas_instruments/DAC81404/datasheet.toml``, generated in the example's directory.

The reader cannot see the device's internal clocks, so every value is against the edge of the clock the device forwards, at its pin.
Vivado's ``report_datasheet`` gives each port against the clock that enters the device, which the reader cannot see, and leaves out the time between the launch and capture edges the interface file chooses.

The file
--------

The datasheet is a TOML file.
The text for the reader is the multi-line string ``document``, at the top of the file, and each port is a ``[[pin]]`` table.
stacv does not read the file.

:Title: The interface and design, the stacv version, the device and speed grade, the timing tool and the process corners, from the header of the timing reports.
:Section 1, References: The md5sum of the interface, part and traces files, and of each timing report.
:Section 2, Timing: Each port's symbols and values, with notes on what the values are against.
:Sections 3 on: One section for each port, in the order of the ``[[port]]`` tables, with a drawing of its values against its clock edge.

The ``[[pin]]`` tables have the form of the pins of a :doc:`part file <part>`, from the device's view as the part, so a design that connects to the device can copy them into its part file.
Each value's ``source`` is the section that draws it.

.. code-block:: toml

   [[pin]]
   name = "O_DAC_DATA"
   methodology = "SDR-SS-O"
   clock = {pin = "O_DAC_SCLK", max_frequency = 25}
   launch_edge = "Rising"
   cko_max = {value = 0.689, symbol = "tCOmax", source = "Section 3"}
   cko_min = {value = -0.908, symbol = "tCOmin", source = "Section 3"}

Values
------

Each value is the worst of every timing report of the port: the worst setup report and the worst hold report, whichever process corner they are from.
The values keep the clock uncertainty and the clock pessimism removal of the timing reports.
Vivado's ``report_datasheet`` leaves out the clock pessimism removal, so its values are more conservative by that amount, 0.22 to 0.27 ns in the DAC81404 example.

=============  ==========  =====================  =============================================================================
Methodology    Symbol      Part file key          Value
=============  ==========  =====================  =============================================================================
SDR-SS-O       tCOmin      ``cko_min``            hold requirement + hold slack - minimum output delay
\              tCOmax      ``cko_max``            setup requirement - setup slack - maximum output delay
SDR-SS-O-FLC   tB          ``valid_before``       setup slack + maximum output delay
\              tA          ``valid_after``        hold slack - minimum output delay
SDR-SS-RT-DI   tSU         ``setup``              half a period - (maximum input delay + setup slack)
\              tH          ``hold``               (minimum input delay - hold slack) + setup requirement - hold requirement - half a period
=============  ==========  =====================  =============================================================================

* **SDR-SS-O**: the clock to out is from the clock edge the data is launched with, so each launch edge must be at an edge of the forwarded clock, the same kind for setup and hold (generate_011).
  The data changes between tCOmin and tCOmax after that edge.
* **SDR-SS-O-FLC**: the time the signal is valid before the first capture edge and after the last.
* **SDR-SS-RT-DI**: the device captures with its own clock, which the reader cannot see, so the setup and hold are to the next edge of the forwarded clock after the launch edge, half a period later.
  The section also gives when the device captures, and when the data must be stable, from the launch edge.

The setup and hold requirements and the port delays are the same in every report of a port, so the worst slack gives the worst value.
A value from SDR-SS-O whose launch and capture edges are different kinds, or from SDR-SS-RT-DI, is moved from one edge of the clock to the other.
The notes then say that the rising and falling edges of the clock are assumed to leave the device with the same delay.

The values hold only for the clock frequency the device forwards, which the reader cannot change.

Symbols
-------

Each methodology has fixed symbols, in the table above.
A symbol that more than one port gives is numbered with ``_<n>``, in the order of the ports: two SDR-SS-O ports give tCOmin_1 and tCOmax_1, then tCOmin_2 and tCOmax_2.
A port's symbols share its number.
A symbol only one port gives has no number.

The numbers follow the order of the ``[[port]]`` tables, so adding or moving a port can change them.
The ``[[pin]]`` tables name the pin of each symbol, for a tool that reads them.

Drawings
--------

Each port's section draws its values against its clock edge.
The drawing is not to scale: the edge and each value are placed in time order, a fixed number of columns apart, so each value is on the side of the edge its sign puts it.

.. code-block:: text

                                     ____________________
     O_DAC_SCLK  ____________________/

                      |<-- tCOmin -->|<-- tCOmax -->|
                 _____ _____________________________ _____
     O_DAC_DATA  _____X#############################X_____

=========  ===============================================================================
Character  Meaning
=========  ===============================================================================
``_``      In the data, where it is valid.
``#``      Where the data may change.
``X``      The limit a value gives.
``|<->|``  The value with its symbol, from the clock edge.
=========  ===============================================================================

Arrows either side of the edge share a row; arrows on the same side each have a row, the longer above the shorter.
SDR-SS-O-FLC has two drawings: tB before the first edge, and tA after the last.

Ports left out
--------------

Every port of the interface is accounted for.
A port with no section is listed under the Timing table, with the reason:

.. code-block:: text

   These ports are not in this datasheet:

     O_DAC_LDAC  deferred
     I_MII_RXD   SDR-SS-I, which stacv cannot write a datasheet for yet

Not supported yet
-----------------

* Methodologies other than SDR-SS-O, SDR-SS-O-FLC and SDR-SS-RT-DI.
* The derivation of each value, per process corner, which is planned as a separate report.

Errors
------

``stacv generate datasheet`` stops with an error, and writes no datasheet, when an SDR-SS-O port's launch edge is not at an edge of its forwarded clock, or its setup and hold launch edges are at different kinds of edge (generate_011).
Errors in a timing report stop it as they stop ``stacv check``.
