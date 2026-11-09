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

2. **Fill in `spi_config.toml`** from the HDL.  Replace every `FROM_DESIGN_...`; each placeholder is named
   after its table and key, such as `FROM_DESIGN_SCK_PORT`, so each can be replaced on its own:
   - `[device_clock] name`: the clock the SPI logic runs on, as the board constraints name it
     (`create_clock -name ...`).
   - `port` of `[sck]`, `[copi]`, `[cipo]`, `[cs]`: the top-level ports.  COPI is data into the part, CIPO
     data out of it.
   - `register`: the register that drives the port (SCK, COPI, CS) or captures it (CIPO), named as Vivado
     names it after synthesis: hierarchy separated by `/`, `_reg` added, a bus bit in brackets, such as
     `u_spi/rx_shift_reg[0]`.  Exactly the bit the design uses: for a receive shift register, the bit the
     port shifts into, which is the only one with a path from the port.
   - `[sck] read_period`: only when the design reads at a slower SCK than it writes (the part's CIPO allows
     a lower frequency).  COPI and CS are then timed on SCK and CIPO on the read SCK, so give the CS edges
     for the access with the least time to the SCK edge, usually the faster write.
   - `source` in `[device_clock]` and `[sck]`, optional: where the periods come from.
   - `name`: any name for the interface; it names the timing reports.
   - `timing_reports_dir`: where the report script writes the reports, relative to `spi_config.toml`.

3. **Fill in `part.toml`** from the part's datasheet.  Read it as text with `pdftotext -layout <file>.pdf -`,
   which keeps table columns aligned; `-f` and `-l` pick the first and last page.  The interface timing
   table is often split across two pages; read both.  Replace every `FROM_DATASHEET_...`: each `value` with a
   number (ns, or MHz for `max_frequency`), its `symbol` with the datasheet's (such as `"tOD"`), and its
   `source` with where it is: the document, its section and page, such as `"SBASAO8A section 6.9, page 27"`.  Rename the pins to the datasheet's names; the traces
   file keeps its own.  Do not change the keys below the `#--- set by stacv ...` lines.
   - COPI pin: `setup` and `hold` to the SCK sample edge.
   - CS pin: chip-select setup and hold (tCSS, tCSH).
   - CIPO pin: `cko_max` and `cko_min`, the clock-to-out from the SCK change edge.  If the datasheet also
     gives the time to drive CIPO out of high impedance (such as tOZD), use the worse of the two.
   - stacv does not check the SCK period, its high and low times, or the gap CS stays high between accesses
     (such as tP, tPH, tPL and tIAG), and does not yet check `max_frequency`: check them by hand.

4. **Fill in `traces.toml`** from the board: `{max_delay = ..., min_delay = ...}` in ns for each trace, or
   leave `{}` to use `default_delay`.

5. **Set the edges.**  Each edge in `spi_config.toml` says when the HDL launches or captures a signal, in
   device clock periods from a named edge of SCK, with where in the HDL it comes from:

   ```
   assert = {sck_edge = "first sample", clocks = -4, source = "spi_master.vhd: IDLE clears scs_n_q 4 clocks before sclk_q rises"}
   ```

   - `[copi] launch`, from `"change"`: the SCK change edge before the sample edge that captures the bit.
     Count it from the bits between the first and the last; the first bit is often set earlier, with CS,
     which the CS edges cover.
   - `[cipo] capture`, from `"sample"`: the SCK sample edge after the change edge the part launches on;
     0 is the device clock edge that makes that SCK edge.
   - `[cs] assert`, from `"first sample"`: the first SCK sample edge of the transfer.
   - `[cs] deassert`, from `"last change"` or `"last sample"`: the last SCK edge of that kind.

   `clocks` counts as the state machine does: -4 is four device clock periods before the SCK edge, 0.5 half a
   period after it (a falling-edge register).  The template's values are the usual ones for the mode, and
   the comments give each edge's time in ns; trace the state machine for one access and correct them.
   Every `source` must be filled in.  Then check:

   ```
   bin/stacv visualize edges spi_config.toml          # launch and capture edges, setup and hold requirements
   bin/stacv visualize block_diagram spi_config.toml  # ports, registers and traces, to catch swapped names
   ```

   A negative hold requirement means the signal changes after the edge that captures it.  For CS, the
   drawing measures it from the last sample edge, whichever edge `deassert` counts from: CS deasserted 4
   clocks after the last change edge of an 80 ns SCK shows as -80 ns (40 ns + 40 ns).

6. **Generate** the constraints and the report script, from the folder holding `spi_config.toml`:

   ```
   bin/stacv generate xdc spi_config.toml --output interface.xdc
   bin/stacv generate report_tcl spi_config.toml --output report.tcl
   ```

   The XDC explains every constraint.  Do not edit it; change the TOML files and generate it again.

7. **Run Vivado.**  Read `interface.xdc` after the board constraints and after `synth_design`
   (synthesis does not use I/O timing and warns about each `-reference_pin`).  After routing, `cd` to the
   folder holding `spi_config.toml` and `source report.tcl`: the report paths are relative to that folder,
   and the script creates the report folder.  A non-project run, from the folder holding `spi_config.toml`:

   ```
   foreach f [glob <hdl folder>/*.vhd] { read_vhdl -vhdl2008 $f }
   read_xdc <board constraints>.xdc
   synth_design -top <top> -part <part>
   read_xdc interface.xdc
   opt_design; place_design; route_design
   source report.tcl
   ```

8. **Check the reports:**

   ```
   bin/stacv check spi_config.toml
   ```

   One line per port: `PASSED: <port>.<methodology>` with its worst setup and hold slack, or
   `FAILED: [<rule>] <port>.<methodology>` with the file and line of each finding; `Check Passed` when
   all pass.  Exit code 0 when all pass, 1 when a rule
   fails, 2 on an input error.  Fix a failure in the TOML files or the design, never in the XDC, and run
   steps 6 to 8 again.

   For the margin in each corner, and where the data sits in its eye, `bin/stacv visualize eye
   spi_config.toml` prints it for each data port.

## The workflow for an RMII interface

The device (the FPGA) is the MAC; the part is the PHY.  RMII fixes REF_CLK at 50 MHz and every edge (launch
and capture on its rising edge, at both ends), so there are no edges or periods to set.

1. `bin/stacv create template rmii --output <folder>` writes `rmii_config.toml`, `part.toml` and
   `traces.toml`.
2. In `rmii_config.toml`, replace every `FROM_DESIGN_...`: `[ref_clk]` `name` (the clock's name in the
   constraints) and `port`, and the `port` and `register` of `[txd]`, `[tx_en]`, `[rxd]` and `[crs_dv]`.
   `[tx_er]` and `[rx_er]` are optional: if the design does not use one, remove its table here and its
   trace in `traces.toml`.
3. In `part.toml`, the PHY's RMII timing: setup and hold of TXD, TX_EN and TX_ER, and the output delay
   (`cko_max`, `cko_min`) of RXD, CRS_DV and RX_ER, all to the rising edge of REF_CLK.  If the datasheet
   gives only a maximum output delay, use 0 as the minimum.
4. In `traces.toml`, each trace's delays.  REF_CLK reaches each end on its own trace from its source (the
   PHY, the MAC or an oscillator): `ref_clk_to_device` names the port it arrives on, `ref_clk_to_part` the
   PHY's clock pin; give each its delay from the source.
5. `bin/stacv visualize block_diagram rmii_config.toml`, then generate, run Vivado and check as for SPI
   (steps 6 to 8 above), with `rmii_config.toml` in place of `spi_config.toml`.


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
