* Claim 1: Sweep Vctrl to measure R_eff of FGMOS in ohmic region
* Run: ngspice -b claim1_rtl_sweep.sp

.include sky130_tt_params.sp
.include fgmos_sky130_subckt.sp

* Test circuit: FGMOS_3IN with all inputs at 0V, sweep Vctrl
Vcc  vcc  0  DC 1.8
Vds  drain 0  DC 50m        ; small Vds to stay in ohmic
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
wrdata ../data/claim1_ngspice_sweep.csv v(drain) i(Vds)
.endc

.end
