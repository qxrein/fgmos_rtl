###############################################################################
# Created by write_sdc
###############################################################################
current_design fgmos_rtl_wrapper
###############################################################################
# Timing Constraints
###############################################################################
create_clock -name clk -period 20.0000 [get_ports {clk}]
set_propagated_clock [get_clocks {clk}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_a[0]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_a[1]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_a[2]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_b[0]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_b[1]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_b[2]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[0]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[1]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[2]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[3]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[4]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[5]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[6]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vctrl[7]}]
set_input_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {rst_n}]
set_output_delay 4.0000 -clock [get_clocks {clk}] -add_delay [get_ports {pad_vout}]
###############################################################################
# Environment
###############################################################################
set_load -pin_load 0.0334 [get_ports {pad_vout}]
###############################################################################
# Design Rules
###############################################################################
set_max_fanout 10.0000 [current_design]
