# Minimal OpenROAD RTL-to-layout flow for small baseline blocks (sky130_fd_sc_hd, TT 25C 1.8V).
set top $::env(TOP)
set pdk $::env(PDK_ROOT)/sky130A
set lib $pdk/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
read_lef $pdk/libs.ref/sky130_fd_sc_hd/techlef/sky130_fd_sc_hd__nom.tlef
read_lef $pdk/libs.ref/sky130_fd_sc_hd/lef/sky130_fd_sc_hd.lef
read_liberty $lib
read_verilog out/$top.syn.v
link_design $top

# constraints: data inputs toggle against a 100 MHz virtual clock; the config chain is
# loaded once and then held static (cfg_clk gated off), as in operation.
create_clock -name vclk -period 10
set data_in [delete_from_list [all_inputs] [get_ports -quiet {cfg_clk cfg_in}]]
set_input_delay 0 -clock vclk $data_in
set_output_delay 0 -clock vclk [all_outputs]
set_case_analysis 0 [get_ports -quiet cfg_clk]
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_2 -pin Y [all_inputs]
set_load 0.005 [all_outputs]

initialize_floorplan -utilization $::env(UTIL) -aspect_ratio 1 -core_space 2 -site unithd
source $::env(TRACKS_TCL)
place_pins -hor_layers met3 -ver_layers met2
tapcell -distance 14 -tapcell_master sky130_fd_sc_hd__tapvpwrvgnd_1 -endcap_master sky130_fd_sc_hd__decap_3
global_placement -density 0.6 -skip_initial_place
detailed_placement
check_placement
estimate_parasitics -placement
set_wire_rc -signal -layer met2
set_wire_rc -clock -layer met3
global_route -allow_congestion
detailed_route -output_drc out/$top.route_drc.rpt -verbose 0
estimate_parasitics -global_routing

set fh [open out/$top.metrics.txt w]
set core [ord::get_die_area]
puts $fh "design $top"
puts $fh "die_area_um [ord::get_die_area]"
puts $fh "core_area_um [ord::get_core_area]"
set inst_area 0
set n 0
set nflop 0
foreach inst [get_cells *] {
  set m [get_property $inst ref_name]
  if {[string match "*tapvpwrvgnd*" $m] || [string match "*decap*" $m] || [string match "*fill*" $m]} {continue}
  set inst_area [expr {$inst_area + [get_property [get_lib_cells */$m] area]}]
  incr n
  if {[string match "*df*" $m]} {incr nflop}
}
puts $fh "std_cell_area_um2 $inst_area"
puts $fh "num_cells $n"
puts $fh "num_flops $nflop"
close $fh
report_checks -path_delay max -from $data_in -to [all_outputs] -format full_clock_expanded -digits 4 > out/$top.timing.rpt
set_power_activity -input_ports $data_in -activity 0.5
set_power_activity -input_ports [get_ports -quiet {cfg_clk cfg_in}] -activity 0.0
report_power -digits 6 > out/$top.power.rpt
write_def out/$top.def
