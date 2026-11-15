* Transient switching: one input high, CL=80fF, Sky130 BSIM4 nfet_01v8
* FGMOS pull-up + three parallel pull-down nfet_01v8 (W=2um, L=150nm)

.option scale=1.0u
.option ngbehavior=ltpsa
.param MC_MM_SWITCH=0
.param mc_mm_switch=0
.include PDK_NFET_TT
.include fgmos_sky130_bsim4_subckt.sp
.include sky130_tt_params.sp

Vcc vcc 0 DC 1.8
Vctrl vctrl 0 DC 0.65
VA va 0 PULSE(0 1.8 1n 50p 50p 5n 10n)
VB vb 0 DC 0
VC vc 0 DC 0

X1 vcc fg_node out 0 va vb vc vctrl FGMOS_3IN
M_A out va 0 0 sky130_fd_pr__nfet_01v8 W=2 L=0.15
M_B out vb 0 0 sky130_fd_pr__nfet_01v8 W=2 L=0.15
M_C out vc 0 0 sky130_fd_pr__nfet_01v8 W=2 L=0.15
Cload out 0 80f

.tran 1p 12n

.control
run
set wr_vecnames
set wr_singlescale
wrdata ../data/claim_transient_bsim4.csv v(out) v(va) v(fg_node)
.endc

.end
