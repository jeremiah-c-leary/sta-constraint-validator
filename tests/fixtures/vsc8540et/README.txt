The VSC8540ET example's TOML files as they were before its RMII interface was linked by signal
(2026-11-08).  The part coverage and rule tests use them: they remove and change ports and
traces of the pin-linked RMII interface, which the signal-linked example would stop on earlier.
The timing reports are still read from example/microchip/vsc8540et/timing_reports.
