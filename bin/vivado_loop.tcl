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
#   report_dir  directory the report script runs in, so its relative paths
#               resolve as stacv check resolves them; "" for out_dir
#
# A step that fails prints one "ERROR: [vivado_loop]" line with the reason,
# for bin/vivado_loop to show, and exits.
################################################################################
lassign $argv design_tcl out_dir if_xdc report_tcl report_dir

proc run_step {sStep sScript} {
    if {[catch {uplevel #0 $sScript} sMessage]} {
        puts "ERROR: \[vivado_loop\] $sStep failed: $sMessage"
        exit 1
    }
}

set design_dir [file dirname [file normalize $design_tcl]]
run_step "reading the design file" {source $design_tcl}
file mkdir $out_dir

run_step "reading the sources" {
    foreach f $design_vhdl {
        read_vhdl -vhdl2008 [file join $design_dir $f]
    }
    foreach f $design_xdc {
        read_xdc [file join $design_dir $f]
    }
    if {$if_xdc ne ""} {
        # The interface constraints are I/O timing only, which synthesis does not use;
        # it warns about each -reference_pin, so they are kept for implementation.
        read_xdc $if_xdc
        set_property USED_IN_SYNTHESIS false [get_files $if_xdc]
    }
}

run_step "synthesis"      {synth_design -top $design_top -part $design_part}
run_step "opt_design"     {opt_design}
run_step "place_design"   {place_design}
run_step "route_design"   {route_design}

run_step "writing the checkpoint and summary reports" {
    write_checkpoint -force [file join $out_dir routed.dcp]
    report_timing_summary -file [file join $out_dir timing_summary.rpt]
    check_timing -file [file join $out_dir check_timing.rpt]
}

if {$report_tcl ne ""} {
    if {$report_dir eq ""} {
        set report_dir $out_dir
    }
    run_step "the report script $report_tcl" {
        set sBuildDir [pwd]
        cd $report_dir
        source $report_tcl
        cd $sBuildDir
    }
}

puts "vivado_loop: Vivado steps finished"
