* FGMOS 3-input subcircuit built from Sky130 NMOS + capacitors
* Ports: drain, fg_node, source, body, IN1, IN2, IN3, VCTRL
* All caps within Sky130 MIM range (10fF each)

.subckt FGMOS_3IN drain fg_node source body IN1 IN2 IN3 VCTRL
+ PARAMS: C1=10f C2=10f C3=10f CFG=5f CSB=3f CDB=2f Q0=0

* Core NMOS using behavioral BSIM-like model 
* (replace with sky130_fd_pr__nfet_01v8 if PDK installed)
M1 drain fg_node source body NMOS_SKY130 W=2u L=150n

* Capacitive weight bus — coupling network
C_in1  IN1   fg_node  {C1}
C_in2  IN2   fg_node  {C2}
C_in3  IN3   fg_node  {C3}
C_ctrl VCTRL fg_node  {CFG}
C_sb   source fg_node {CSB}
C_db   drain  fg_node {CDB}

* Residual charge as initial condition (for p-bit simulations)
* Q0 modeled as equivalent voltage offset: Vq0 = Q0/CT
.ic V(fg_node) = {Q0 / (C1+C2+C3+CFG+CSB+CDB)}

.ends FGMOS_3IN

* Behavioral NMOS model (Sky130 tt-corner approximation)
.model NMOS_SKY130 NMOS LEVEL=1
+ VTO=0.49 KP=270e-6 LAMBDA=0.01 GAMMA=0.5 PHI=0.65
