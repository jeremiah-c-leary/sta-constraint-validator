################################################################################
# vivado_loop.tcl
#
# Non-project Vivado flow used by bin/vivado_loop:
#   synthesis, place and route of a design, then the stacv report script.
#
# Arguments (-tclargs):
#   design_tcl  design description: sets design_top, design_part,
#               design_vhdl and design_xdc, paths relative to itself
#   out_dir     directory for the checkpoint and the summary reports
#   if_xdc      interface constraints file, or "" for none
#   report_tcl  stacv report script, or "" for none
################################################################################
lassign $argv design_tcl out_dir if_xdc report_tcl

set design_dir [file dirname [file normalize $design_tcl]]
source $design_tcl
file mkdir $out_dir

foreach f $design_vhdl {
    read_vhdl -vhdl2008 [file join $design_dir $f]
}
foreach f $design_xdc {
    read_xdc [file join $design_dir $f]
}
if {$if_xdc ne ""} {
    read_xdc $if_xdc
}

synth_design -top $design_top -part $design_part
opt_design
place_design
route_design

write_checkpoint -force [file join $out_dir routed.dcp]
report_timing_summary -file [file join $out_dir timing_summary.rpt]
check_timing -file [file join $out_dir check_timing.rpt]

if {$report_tcl ne ""} {
    source $report_tcl
}

puts "vivado_loop: Vivado steps finished"
