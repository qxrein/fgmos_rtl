* grid
.lib "/Users/rein/projects/fgmos_rtl/.eda/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice" tt
.option scale=1.0u
.param n=0
Vcc vcc 0 1.8
Vctrl vctrl 0 0.9
Bfg fg 0 V = (8f*1.8*n + 30f*v(vctrl))/(24f+30f+3f)
XMp out fg vcc vcc sky130_fd_pr__pfet_01v8 W=6 L=0.15
Va a 0 {1.8*(n>=1)}
Vb b 0 {1.8*(n>=2)}
Vc c 0 {1.8*(n>=3)}
XMa out a 0 0 sky130_fd_pr__nfet_01v8 W=0.65 L=0.15
XMb out b 0 0 sky130_fd_pr__nfet_01v8 W=0.65 L=0.15
XMc out c 0 0 sky130_fd_pr__nfet_01v8 W=0.65 L=0.15
.control
foreach nn 0 1 2 3
  alterparam n = $nn
  reset
  dc Vctrl 0 1.8 0.02
  set fname = g_n{$nn}.txt
  wrdata $fname v(out)
end
.endc
.end
