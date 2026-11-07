################################################################################
# dac39rf20_board.xdc
#
# Board constraints for dac39rf20_top on xc7a12tcpg238-2: the system clock and
# the pin assignments.  The DAC39RF20 CMOS pins run from VDDIO = 1.8 V, so
# bank 34 is powered at 1.8 V.
#
# The SPI interface timing constraints are NOT in this file; they belong to
# the interface constraints file.
################################################################################

# System clock: 100 MHz oscillator on a clock-capable pin
create_clock -name sys_clk -period 10.000 [get_ports clk_100m]
set_property -dict {PACKAGE_PIN P3 IOSTANDARD LVCMOS18} [get_ports clk_100m]

# Push button, asynchronous (synchronised inside the design)
set_property -dict {PACKAGE_PIN K2 IOSTANDARD LVCMOS18} [get_ports btn_reset]
set_false_path -from [get_ports btn_reset]

# DAC39RF20 standard SPI interface
set_property -dict {PACKAGE_PIN N2 IOSTANDARD LVCMOS18} [get_ports dac_sclk]
set_property -dict {PACKAGE_PIN N3 IOSTANDARD LVCMOS18} [get_ports dac_sdi]
set_property -dict {PACKAGE_PIN P2 IOSTANDARD LVCMOS18} [get_ports dac_sdo]
set_property -dict {PACKAGE_PIN P1 IOSTANDARD LVCMOS18} [get_ports dac_scs_n]

# DAC39RF20 reset, static after start-up
set_property -dict {PACKAGE_PIN M1 IOSTANDARD LVCMOS18} [get_ports dac_resetn]
set_false_path -to [get_ports dac_resetn]

# Status LEDs
set_property -dict {PACKAGE_PIN L1 IOSTANDARD LVCMOS18} [get_ports led_done]
set_property -dict {PACKAGE_PIN L3 IOSTANDARD LVCMOS18} [get_ports led_id_ok]
set_false_path -to [get_ports {led_done led_id_ok}]
