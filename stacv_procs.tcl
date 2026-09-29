
# Example procedure to generate setup and hold reports at all corners in a single file
proc stacv_generate_quartus_timing_file {to fileName} {

  set operating_conditions [get_operating_conditions -for_analysis]

  foreach operating_condition $operating_conditions {
	set_operating_conditions $operating_condition
	report_timing -to [get_ports $to] -setup -file $fileName -detail full_path -append -extra_info all
	report_timing -to [get_ports $to] -hold -file $fileName -detail full_path -append -extra_info all
  }
}

# Example procedure to generate setup and hold reports at all corners in a single file
proc stacv_generate_vivado_timing_file {to fileName} {
	config_timing_corners -corner Slow -delay_type min_max
	config_timing_corners -corner Fast -delay_type none
	report_timing -to [get_ports $to] -setup -file $fileName -append -path full_clock_expanded
	report_timing -to [get_ports $to] -hold -file $fileName -append -path full_clock_expanded

	config_timing_corners -corner Fast -delay_type min_max
	config_timing_corners -corner Slow -delay_type none
	report_timing -to [get_ports $to] -setup -file $fileName -append -path full_clock_expanded
	report_timing -to [get_ports $to] -hold -file $fileName -append -path full_clock_expanded
}