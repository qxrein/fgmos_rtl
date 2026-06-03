* Auto-generated post-layout R_eff sweep (Sky130 TT + extracted layout)
.option scale=1.0u
.option ngbehavior=ltpsa
.param MC_MM_SWITCH=0
.param mc_mm_switch=0
.include "../../share/pdk/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical.spice"
.include "../../share/pdk/sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical__lin.spice"
.include "../../share/pdk/sky130A/libs.tech/ngspice/sky130_fd_pr__model__r+c.model.spice"
.include "../../share/pdk/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
.include "../../share/pdk/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.pm3.spice"
.include "../../share/pdk/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__cap_mim_m3_1.model.spice"
.include "fgmos_rtl_cell_extracted_sanitized.spice"

* Bench: extracted pull-up device; sweep effective gate bias
Vdd vdd 0 DC 1.8
Vss vss 0 DC 0
Vds vout 0 DC 0.05
Vfg fg 0 DC 0.9

* Pin order from extracted .subckt line (regenerated after each extract)
Xpl vss vout vss fg fg fg fgmos_rtl_cell

.dc Vfg 0.55 1.25 0.02
.control
run
set wr_vecnames
set wr_singlescale
wrdata ../data/postlayout_reff_sweep.csv v(fg) v(vout) i(Vds)
.endc
.end
