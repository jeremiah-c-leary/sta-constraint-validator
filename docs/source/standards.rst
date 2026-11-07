Interface Standards
===================

Many interfaces follow a standard, such as SPI, whose signals each have a name and a role.
An interface file, and the part interface it connects to, can name the standard they follow; each clock, port, part pin and trace then names the signal it carries.
The signals link the three files together, and let stacv check the interface against the standard.

The keys
--------

====================  ======================================  ================================================================
Key                   Where                                   Description
====================  ======================================  ================================================================
``if_standard``       interface file, part ``[[interface]]``  The standard, such as ``"SPI mode 1"``.
``if_role``           interface file, part ``[[interface]]``  The role of the device, or of the part: ``"controller"`` or ``"peripheral"``.
``if_signal``         ``[[clock]]``, ``[[port]]``,            The signal of the standard it carries, such as ``"COPI"``.
                      ``[[interface.pin]]``, ``[[trace]]``
====================  ======================================  ================================================================

The role is stated rather than worked out, so that stacv checks it instead of deciding it.

The DAC81404 example follows SPI mode 1, with the device as the controller:

.. code-block:: toml

   # interface.toml
   if_standard = "SPI mode 1"
   if_role = "controller"

   [[port]]
   name = "O_DAC_DATA"
   methodology = "SDR-SS-O"
   if_signal = "COPI"

   # part.toml
   [[interface]]
   name = "Serial Interface"
   if_standard = "SPI mode 1"
   if_role = "peripheral"

   [[interface.pin]]
   name = "SDIN"
   methodology = "SDR-SS-I"
   if_signal = "COPI"

   # traces.toml
   [[trace]]
   name = "data_output"
   if_signal = "COPI"
   device_to_part = {max_delay = 3.00, min_delay = 1.00}

Keep ``if_signal`` as it is when renaming ports and pins: it is what links them.
A changed signal is reported as an error, not used silently.

Linking
-------

A trace that gives ``if_signal`` gives no ``device_pin`` or ``part_pin``: it runs from the port, or the ``port`` of the clock, with that signal to the part pin with that signal.
A trace gives ``if_signal``, or ``device_pin`` and ``part_pin``, not both (traces_config_011).
An interface that follows no standard links its traces by pin names, as before.

The clock pin of the part has its own ``[[interface.clock_pin]]`` table, with ``name`` and ``if_signal``, and the part's pins name it as their clock by its signal, ``clock = {if_signal = "SCK", ...}`` (see :doc:`part`).
With the traces linked by signal too, nothing refers to a part pin's name, so a part file from a library can be used as it is.

Signal names
------------

* Each signal is carried by one port, part pin and trace.
  The clocks of one port may share a signal: the DAC81404 writes on ``dac_sclk`` and reads on the slower ``dac_sclk_rd``, both on ``O_DAC_SCLK`` and both ``SCK``.
* A signal that can repeat, such as the chip select of a bus with several parts, is numbered with a dot: ``CS.1``, ``CS.2``.
  Brackets are left for the bits of a bus, such as ``TXD[3:0]``.
* Clocks that stay inside the device give no ``if_signal``.

SPI
---

The signal names are the Open Source Hardware Association's (2020).
Each names the signal from the bus's view, so the same name is right in all three files: COPI is the controller's output and the peripheral's input.

========  =======  ===================  ===========
Signal    Kind     Driven by            Repeats
========  =======  ===================  ===========
SCK       clock    controller           No
COPI      data     controller           No
CIPO      data     peripheral           No
CS        data     controller           Yes
========  =======  ===================  ===========

The mode sets the level the clock idles at (CPOL) and the edges data changes and is sampled on (CPHA).
The leading edge is the first edge of a transfer.

==========  ====  ====  ==========  ==================  ==================
Standard    CPOL  CPHA  Clock idle  Data changes on     Data sampled on
==========  ====  ====  ==========  ==================  ==================
SPI mode 0  0     0     low         falling (trailing)  rising (leading)
SPI mode 1  0     1     low         rising (leading)    falling (trailing)
SPI mode 2  1     0     high        rising (trailing)   falling (leading)
SPI mode 3  1     1     high        falling (leading)   rising (trailing)
==========  ====  ====  ==========  ==================  ==================

Checks
------

Every command that reads the traces and part files with the interface file runs the checks, before anything else: ``stacv check``, ``stacv generate xdc``, and ``stacv visualize block_diagram`` and ``eye``.

* The standard, the role and each signal are ones the standard has (if_standard_002, if_standard_003, if_standard_004).
  A file that gives a signal names a standard (if_standard_001).
* Each signal is carried once in each file (if_standard_005).
* The part interface follows the same standard, in the other role (if_standard_006).
* Every signal of the standard has a port or clock, a part pin, and a trace (if_standard_009), and each trace's signal has a port or clock (if_standard_007) and a part pin (if_standard_008).
* Each signal goes the way its driver sends it (if_standard_010, if_standard_011):

  * a trace gives ``device_to_part`` when the device drives the signal, and ``part_to_device`` when the part does;
  * an analyzed port's methodology times an output when the device drives the signal, and an input when the part does;
  * a part pin is an output when the part drives the signal, and an input when the device does.

* Each signal changes and is sampled on the edges of the mode (if_standard_012):

  * a clock with a signal and an ``idle`` idles at the mode's level;
  * a port's edges on the clock it forwards are the mode's sample edges when the clock captures, and its change edges when the clock launches;
  * a part input captures on the sample edge, and a part output launches on the change edge.

Not supported yet
-----------------

* Standards other than SPI.
* Traces from a clock source with ``if_signal`` (traces_config_011).
