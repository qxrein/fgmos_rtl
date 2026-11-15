* Claim 1: R_eff DC sweep, Sky130 BSIM4 nfet_01v8, W=2um L=150nm
* Generated/used by run_bsim4_sky130.sh — do not include PDK paths by hand.

.option scale=1.0u
.option ngbehavior=ltpsa
.param MC_MM_SWITCH=0
.param mc_mm_switch=0
.include PDK_NFET_TT
.include fgmos_sky130_bsim4_subckt.sp
.include sky130_tt_params.sp

Vcc  vcc  0  DC 1.8
Vds  drain 0  DC 50m
Vin1 in1  0  DC 0
Vin2 in2  0  DC 0
Vin3 in3  0  DC 0
Vctrl vctrl 0 DC 0

X1 drain fg_node 0 0 in1 in2 in3 vctrl FGMOS_3IN

.dc Vctrl 0.5 1.5 0.01

.control
run
set wr_vecnames
set wr_singlescale
wrdata ../data/claim1_ngspice_bsim4_sweep.csv v(drain) v(fg_node) i(Vds)
.endc

.end
