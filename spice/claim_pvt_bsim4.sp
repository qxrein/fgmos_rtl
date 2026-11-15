* NOR-band tau proxy: DC R_eff at Vctrl=0.65, one input high, CL=80fF implied in post-process
.option scale=1.0u
.option ngbehavior=ltpsa
.param MC_MM_SWITCH=0
.param mc_mm_switch=0
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
run
set wr_vecnames
set wr_singlescale
wrdata ../data/claim_pvt_bsim4.csv v(drain) v(fg_node) i(Vds)
.endc

.end
