* Claim 2: Test NOR/MAJ/AND modes via Vctrl sweep
* Run: ngspice -b claim2_logic_modes.sp

.include sky130_tt_params.sp
.include fgmos_sky130_subckt.sp

* RTL cell: Vcc -> FGMOS -> out -> NMOS_in -> GND
Vcc vcc 0 DC 1.8
Vctrl vctrl 0 DC 1.0

* Three input NMOS (parallel, driven by A,B,C)
VA va 0 DC 0
VB vb 0 DC 0
VC vc 0 DC 0

* FGMOS load (ohmic resistor)
X1 vcc fg_node out 0 va vb vc vctrl FGMOS_3IN

* Input NMOS transistors
M_A out va  0 0 NMOS_SKY130 W=0.5u L=150n
M_B out vb  0 0 NMOS_SKY130 W=0.5u L=150n
M_C out vc  0 0 NMOS_SKY130 W=0.5u L=150n

* Sweep Vctrl for input combo (1,1,0) = majority test
.dc Vctrl 0.55 1.35 0.01

.control
run
set wr_vecnames
set wr_singlescale
wrdata ../data/claim2_ngspice_logic.csv v(out)
.endc

.end
