* FGMOS_3IN using Sky130 BSIM4 nfet_01v8 (not Level-1)
* Ports: drain, fg_node, source, body, IN1, IN2, IN3, VCTRL
* Device geometry matches the manuscript: W=2um, L=150nm
*
* Requires PDK_ROOT pointing at open_pdks / skywater-pdk sky130A, and:
*   $PDK_ROOT/sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.pm3.spice
* Include the TT (and mismatch, if Monte Carlo) model files in the calling deck
* BEFORE this subcircuit. Use .option scale=1.0u so W=2 L=0.15 are microns.

.subckt FGMOS_3IN drain fg_node source body IN1 IN2 IN3 VCTRL
+ PARAMS: C1=10f C2=10f C3=10f CFG=5f CSB=3f CDB=2f Q0=0

M1 drain fg_node source body sky130_fd_pr__nfet_01v8 W=2 L=0.15

C_in1  IN1   fg_node  {C1}
C_in2  IN2   fg_node  {C2}
C_in3  IN3   fg_node  {C3}
C_ctrl VCTRL fg_node  {CFG}
C_sb   source fg_node {CSB}
C_db   drain  fg_node {CDB}

.ic V(fg_node) = {Q0 / (C1+C2+C3+CFG+CSB+CDB)}

.ends FGMOS_3IN
