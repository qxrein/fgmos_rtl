* Mismatch Monte Carlo stub (Sky130 nfet_01v8 mismatch corner)
* Enable with mc_mm_switch=1 after including the PDK mismatch file.
.option scale=1.0u
.option ngbehavior=ltpsa
.param MC_MM_SWITCH=1
.param mc_mm_switch=1
.include PDK_NFET_TT
.include fgmos_sky130_bsim4_subckt.sp
.include sky130_tt_params.sp

Vcc vcc 0 DC 1.8
Vds drain 0 DC 50m
Vin1 in1 0 DC 1.8
Vin2 in2 0 DC 0
Vin3 in3 0 DC 0
Vctrl vctrl 0 DC 0.65

X1 drain fg_node 0 0 in1 in2 in3 vctrl FGMOS_3IN

.op

.control
let n = 500
let i = 0
set wr_vecnames
set wr_singlescale
echo "Run via: include mismatch.corner.spice then repeat .op with seeds; see run_bsim4_sky130.sh"
run
wrdata ../data/claim_mismatch_bsim4.csv v(drain) i(Vds)
.endc

.end
