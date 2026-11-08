# AGENTS.md

stacv (sta-constraint-validator) writes the timing constraints of an FPGA's external interfaces, and checks
the timing reports from Vivado against what the interface intends.  You describe the interface in small TOML
files; stacv derives every constraint from them, and checks the reports the same way every time, in
milliseconds.  Use it in place of deriving I/O delays, generated clocks and multicycle paths by hand.

Run it as `bin/stacv <command>` from the repository (Python 3.11 or newer, standard library only).  Every
command prints its help when an argument is missing.

## The workflow for an SPI interface

The device (the FPGA) is the SPI controller; the part is the peripheral.  4-wire SPI, modes 0 to 3.

1. **Create the files** in a folder of their own:

   ```
   bin/stacv create template spi --wires 4 --mode <0-3> --type controller \
       --clock-period <device clock ns> --sck-period <SCK ns> --output <folder>
   ```

   It writes `spi_config.toml`, `part.toml` and `traces.toml`.  SCK must be an even number of device clock
   periods.

2. **Fill in `spi_config.toml`** from the HDL.  Replace every `FROM_DESIGN`:
   - `[device_clock] name`: the clock the SPI logic runs on, as the board constraints name it
     (`create_clock -name ...`).
   - `port` of `[sck]`, `[copi]`, `[cipo]`, `[cs]`: the top-level ports.  COPI is data into the part, CIPO
     data out of it.
   - `register`: the register that drives the port (SCK, COPI, CS) or captures it (CIPO), named as Vivado
     names it after synthesis: hierarchy separated by `/`, `_reg` added, a bus bit in brackets, such as
     `u_spi/rx_shift_reg[0]`.  Exactly the bit the design uses.
   - `name`: any name for the interface; it names the timing reports.
   - `timing_reports_dir`: where the report script writes the reports, relative to `spi_config.toml`.

3. **Fill in `part.toml`** from the part's datasheet.  Replace every `FROM_DATASHEET` with a number (ns, or
   MHz for `max_frequency`) and its `source`, such as `"Table 6.9"`.  Rename the pins to the datasheet's
   names.  Do not change the keys below the `#--- set by stacv ...` lines.
   - COPI pin: `setup` and `hold` to the SCK sample edge.
   - CS pin: chip-select setup and hold (tCSS, tCSH).
   - CIPO pin: `cko_max` and `cko_min`, the clock-to-out from the SCK change edge.

4. **Fill in `traces.toml`** from the board: `{max_delay = ..., min_delay = ...}` in ns for each trace, or
   leave `{}` to use `default_delay`.

5. **Set the edges.**  Each signal is launched and captured on the edges the SPI mode defines.  When the
   HDL launches a signal on a different device clock edge, move it with an adjust key, a whole number of
   device clock edges (+1 is one edge later, +2 one device clock period):
   - `[copi] adjust`: the launch of COPI.  Default: the SCK change edge before the sample edge.
   - `[cs] setup_adjust`: when CS is asserted.  Default: one SCK period before the first sample edge.
   - `[cs] hold_adjust`: when CS is deasserted.  Default: the SCK change edge after the last sample edge.
   - `[cipo] adjust`: the device's capture of CIPO.  Default: at the time of the next SCK sample edge.

   Read the state machine to find the real edges, then check with:

   ```
   bin/stacv visualize edges spi_config.toml          # launch and capture edges, setup and hold requirements
   bin/stacv visualize block_diagram spi_config.toml  # ports, registers and traces, to catch swapped names
   ```

6. **Generate** the constraints and the report script, from the folder holding `spi_config.toml`:

   ```
   bin/stacv generate xdc spi_config.toml --output interface.xdc
   bin/stacv generate report_tcl spi_config.toml --output report.tcl
   ```

   The XDC explains every constraint.  Do not edit it; change the TOML files and generate it again.

7. **Run Vivado.**  Read `interface.xdc` after the board constraints and after `synth_design`
   (synthesis does not use I/O timing and warns about each `-reference_pin`), implement, then, after routing,
   `cd` to the folder holding `spi_config.toml` and `source report.tcl`.  The report paths are relative to
   that folder, and the report folder must exist before the script runs.

8. **Check the reports:**

   ```
   bin/stacv check spi_config.toml
   ```

   One line per port, `PASSED: <port>.<methodology>` or `FAILED: [<rule>] <port>.<methodology>` with the
   file and line of each finding; `Check Passed` when all pass.  Exit code 0 when all pass, 1 when a rule
   fails, 2 on an input error.  Fix a failure in the TOML files or the design, never in the XDC, and run
   steps 6 to 8 again.

## Errors

Input errors are one line on standard error, exit code 2:

```
ERROR: [<identifier>] <file> <message>
```

The message names the key and where it is (for `spi_config.toml`, the table and line), and, after a
semicolon, how to correct it.  Read it and correct the file; do not work around it.

## Other interfaces

An interface that is not SPI is described by hand with an interface file, a part file and a traces file:
`bin/stacv create template interface|part|traces` writes each template.  Every command takes the interface
file in place of `spi_config.toml`.  `bin/stacv generate interface spi_config.toml` shows the interface
file an SPI configuration expands to, as a worked example.

### Choosing the methodology

Each signal is timed by a methodology, and has one at each end.  **A methodology is named from the view of
the file it is in:** the device's view in the interface file (`[[port]] methodology`), the part's view in
the part file (`[[interface.pin]] methodology`).  So the same signal is `SDR-SS-RT-DI` at the device and
`SDR-SS-RT-DO` at the part: the device receives the data, the part sends it.

Answer four questions for each signal, then read its row:

1. Which way does the data go?
2. Where does the clock come from: the device forwards it, the part sends it, or one clock source drives
   both?
3. Is the data launched on a clock that came from the other end (a round trip)?
4. Is it timed on one clock edge per bit, on both edges, or to the first and last edges of a clock that
   stops?

| Data | Clock | Timing | Interface file (device) | Part file (part pin) |
|---|---|---|---|---|
| device to part | the device forwards it | one edge per bit | `SDR-SS-O` | `SDR-SS-I` |
| device to part | the device forwards it, and it stops between transfers | first and last edges, such as a chip select | `SDR-SS-O-FLC` | `SDR-SS-I` |
| device to part | the device forwards it | both edges | `DDR-SS-O` | `DDR-SS-I` |
| device to part | the part sends it; the device launches on it | one edge, round trip | `SDR-SS-RT-DO` | `SDR-SS-RT-DI` |
| part to device | the device forwards it; the part launches on it | one edge, round trip | `SDR-SS-RT-DI` | `SDR-SS-RT-DO` |
| part to device | the part sends it with the data | one edge per bit | `SDR-SS-I` | `SDR-SS-O` |
| part to device | the part sends it with the data | both edges; each edge captures the data aligned with it | `DDR-SS-I-SE` | `DDR-SS-O` |
| part to device | the part sends it with the data | both edges; each edge captures the data the edge before it launched | `DDR-SS-I-NE` | `DDR-SS-O` |
| device to part | one source drives both | one edge per bit | `SDR-SYS-O` | `SDR-SYS-I` |
| part to device | one source drives both | one edge per bit | `SDR-SYS-I` | `SDR-SYS-O` |

A part pin that receives data (`-I`, `RT-DI`) takes `capture_edge`, `setup` and `hold` from the datasheet; a
part pin that sends data (`-O`, `RT-DO`) takes `launch_edge` and either `cko_max`/`cko_min` or
`valid_before`/`valid_after`.  For SPI: COPI is `SDR-SS-O` / `SDR-SS-I`, CS is `SDR-SS-O-FLC` / `SDR-SS-I`,
CIPO is `SDR-SS-RT-DI` / `SDR-SS-RT-DO`.

## Development

- Tests: `bin/gate` runs the unit tests and the documentation build; every commit passes it.
- Style: standard library only; explicit loops, descriptive names, no conditional expressions.
