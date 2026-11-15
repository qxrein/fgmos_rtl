* Diagnostic: is the v1 NMOS pull-up (drain=VCC, source=OUT) ever in triode?
* Triode requires Vds < Vgs - Vth  <=>  VCC - Vout < Vfg - Vout - Vth  <=>  Vfg > VCC + Vth.
* Sweep the gate (floating-gate) voltage with one pull-down ON, read the op-point region.
.lib "/Users/rein/projects/fgmos_rtl/.eda/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
.option scale=1.0u
.temp 27

Vcc vcc 0 1.8
Vfg fg 0 1.0
Va  a   0 1.8
* v1 pull-up: NMOS, drain at VCC, source at OUT
XMpu vcc fg out 0 sky130_fd_pr__nfet_01v8 W=2 L=0.15
* one active pull-down
XMa  out a 0 0 sky130_fd_pr__nfet_01v8 W=2 L=0.15

.control
set wr_singlescale
set wr_vecnames
let vf = 0.5
echo "Vfg  Vout  Vds_pu  Vgs_pu  Vdsat_pu  region" > ../../data/v2/nmos_pullup_region.txt
while vf le 1.8001
  alter Vfg dc = vf
  op
  let vout = v(out)
  let vds  = 1.8 - v(out)
  let vgs  = vf - v(out)
  let vdsat = @m.xmpu.msky130_fd_pr__nfet_01v8[vdsat]
  if vds lt vdsat
    echo "$&vf $&vout $&vds $&vgs $&vdsat triode" >> ../../data/v2/nmos_pullup_region.txt
  else
    echo "$&vf $&vout $&vds $&vgs $&vdsat saturation" >> ../../data/v2/nmos_pullup_region.txt
  end
  let vf = vf + 0.1
end
.endc
.end
