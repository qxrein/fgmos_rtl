* Schematic-aligned netlist for LVS (xschem / ngspice)
* Matches spice/fgmos_sky130_subckt.sp ports

.subckt fgmos_rtl_cell VDD VSS VOUT A B C VCTRL
Xfgmos VOUT FG VSS VSS A B C VCTRL FGMOS_3IN
* Input pull-down stack (simplified — 3 parallel nfet to VSS)
M1 VOUT A VSS VSS sky130_fd_pr__nfet_01v8 W=2u L=0.15
M2 VOUT B VSS VSS sky130_fd_pr__nfet_01v8 W=2u L=0.15
M3 VOUT C VSS VSS sky130_fd_pr__nfet_01v8 W=2u L=0.15
.ends fgmos_rtl_cell

* Include from repo spice/ when running LVS externally:
* .include ../../spice/fgmos_sky130_subckt.sp
