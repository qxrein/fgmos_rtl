"""
K-input QFG threshold-logic cell layout generator (Sky130A, Magic). Usage: python gen_layout_k.py K

Same floorplan rules as the verified K=3 cell (gen_layout.py), generalised:
  * K input MIMs (2x2 um) in one row at a 3.6-um pitch (1.2-um plate gaps for the capm halo);
  * each input pull-down sits under its own plate (gate via in the plate's top margin);
  * reset switch MR and inverter NMOS MIN at the right end of the NFET row, inverter PMOS above MIN;
  * PMOS load with nf = W/4 fingers of 4 um; ballast MIM (9.2 um wide) below the input row;
  * FG on metal 4 (cap top plates, MR drain, load gate), Y_B bus on metal 2, Y jumper on metal 3.
Sizing (load width, ballast length) follows sim/v2/kscale.sizing(K, 0.7, 8(K-1)).
Writes layout/v2k/K<K>/{cells,magic,lvs,klayout}/...
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "sim/v2"))
from kscale import sizing  # noqa: E402
from magparse import parse  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 9
P, _ = sizing(K, 0.7, 8.0 * (K - 1))
NF = int(round(P["wp"] / 4.0))
NAME = f"qfg_tlg_k{K}"
BASE = HERE.parent / "v2k" / f"K{K}"
CELLS, OUT = BASE / "cells", BASE / "magic"
for d in (CELLS, OUT, BASE / "lvs", BASE / "klayout"):
    d.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------ step 1: device cells
(CELLS / "gen_devs.tcl").write_text(f"""load devs -silent
proc gen {{name dev x args}} {{
  box values ${{x}}um 0um ${{x}}um 0um
  magic::gencell sky130::$dev $name {{*}}$args
}}
gen MP  sky130_fd_pr__pfet_01v8 0   w 4.0  l 0.15 nf {NF} conn_gates 1 topc 0 botc 1 viagb 0 viagt 70
gen MIP sky130_fd_pr__pfet_01v8 30  w 1.0  l 0.15 nf 1 topc 0 botc 1 viagb 0 viagt 70
gen MN  sky130_fd_pr__nfet_01v8 40  w 0.42 l 0.15 nf 1 topc 0 botc 1 viagb 0 viagt 70
gen MR  sky130_fd_pr__nfet_01v8 50  w 0.42 l 0.5  nf 1 topc 0 botc 1 viagb 0 viagt 70
writeall force
set f [open devmap.txt w]
foreach inst {{MP MIP MN MR}} {{ puts $f "$inst [instance list celldef $inst]" }}
close $f
puts DONE
quit -noprompt
""")
import os  # noqa: E402
RC = f"{os.environ['PDK_ROOT']}/sky130A/libs.tech/magic/sky130A.magicrc"
for f in list(CELLS.glob("sky130_fd_pr__*.mag")) + [CELLS / "devs.mag", CELLS / "devmap.txt"]:
    if f.exists():
        f.unlink()
subprocess.run(["perl", "-e", "alarm 300; exec @ARGV", "magic", "-dnull", "-noconsole", "-rcfile", RC, "gen_devs.tcl"],
               cwd=CELLS, capture_output=True, text=True)
devmap = dict(l.split() for l in open(CELLS / "devmap.txt"))

cmds = []


def R(layer, x1, y1, x2, y2):
    cmds.append(f"box values {x1:.3f}um {y1:.3f}um {x2:.3f}um {y2:.3f}um; paint {layer}")


def place(kind, inst, cx, cy):
    cell = devmap[kind]
    bb = parse(CELLS / f"{cell}.mag")["bbox"]
    llx, lly = cx + bb[0], cy + bb[1]
    cmds.append(f"box values {llx:.3f}um {lly:.3f}um {llx:.3f}um {lly:.3f}um")
    cmds.append(f"getcell {cell}")
    cmds.append(f"identify {inst}")
    return bb


def label(text, layer, x, y):
    cmds.append(f"box values {x:.3f}um {y:.3f}um {x:.3f}um {y:.3f}um")
    cmds.append(f"label {text} c {layer}")


def mim(x0, y0, w, l, ml=0.2, mr=0.2, mb=0.2, mt=0.2):
    R("metal3", x0 - ml, y0 - mb, x0 + w + mr, y0 + l + mt)
    R("mimcap", x0, y0, x0 + w, y0 + l)
    R("mimcapcontact", x0 + 0.2, y0 + 0.2, x0 + w - 0.2, y0 + l - 0.2)
    R("metal4", x0 + 0.19, y0 + 0.19, x0 + w - 0.19, y0 + l - 0.19)


# ------------------------------------------------------------ capacitors
X0 = [3.6 * i for i in range(K)]
mim(0.2, 0.2, P["bw"], P["bl"], ml=1.0)                       # ballast (bottom plate = VSS)
for x0 in X0:
    mim(x0 + 0.2, 4.35, 2.0, 2.0, mt=0.75)                    # input caps
R("metal4", X0[0] + 0.39, 5.15, X0[-1] + 2.01, 5.55)          # FG bar across the input top plates
R("metal4", 1.0, 0.4 + P["bl"] - 0.5, 1.4, 4.65)              # bar -> ballast top plate
R("via2", -0.66, 0.46, -0.38, 0.74)                           # ballast -> VSS lane
R("metal2", -0.72, 0.40, -0.32, 0.80)
R("metal2", -0.66, 0.40, -0.38, 8.80)

# ------------------------------------------------------------ NFET row
CYN = 7.80
pd_cx = [x0 + 0.9 for x0 in X0]
for i, cx in enumerate(pd_cx):
    place("MN", f"MN{i}", cx, CYN)
MR_CX = pd_cx[-1] + 0.79 + 0.965
MIN_CX = MR_CX + 0.965 + 0.79
place("MR", "MR", MR_CX, CYN)
place("MN", "MIN", MIN_CX, CYN)
X_END = MIN_CX + 0.79
R("metal1", -0.72, 8.525, X_END - 0.03, 8.755)                # VSS rail
R("metal1", -0.72, 8.48, -0.32, 8.80)
R("via1", -0.65, 8.51, -0.39, 8.77)
R("metal2", -0.72, 8.48, -0.32, 8.83)
R("metal2", pd_cx[0] - 0.45, 8.30, MIN_CX + 0.42, 8.56)        # YB bus


def nfet_gate_landing(cx):
    R("metal1", cx - 0.145, CYN - 0.65, cx + 0.48, CYN - 0.215)
    R("via1", cx + 0.16, CYN - 0.60, cx + 0.42, CYN - 0.34)
    R("metal2", cx + 0.06, CYN - 0.66, cx + 0.52, CYN - 0.28)


def d_pad(cx, half=0.0, to_bus=False):
    x1, x2 = cx - 0.38 - half, cx - 0.06 - half
    R("metal1", x1, CYN - 0.03, x2, CYN + 0.35)
    R("via1", x1 + 0.03, CYN + 0.03, x2 - 0.03, CYN + 0.29)
    R("metal2", x1 - 0.03, CYN - 0.03, x2 + 0.03, CYN + (0.76 if to_bus else 0.35))


def s_to_vss(cx):
    R("metal1", cx + 0.105, CYN + 0.30, cx + 0.335, CYN + 0.75)


for i, cx in enumerate(pd_cx):
    nfet_gate_landing(cx)
    R("via2", cx + 0.15, 6.57, cx + 0.43, 6.85)
    R("metal2", cx + 0.10, 6.52, cx + 0.48, 6.90)
    R("metal2", cx + 0.16, 6.52, cx + 0.42, CYN - 0.30)
    d_pad(cx, to_bus=True)
    s_to_vss(cx)
    label(f"I{i}", "metal3", cx + 0.29, 6.95)

cx = MIN_CX                                                    # inverter NMOS
nfet_gate_landing(cx); d_pad(cx); s_to_vss(cx)
R("metal2", cx + 0.16, CYN - 0.66, cx + 0.42, 9.97)
R("via2", cx - 0.36, CYN + 0.02, cx - 0.08, CYN + 0.30)
R("metal3", cx - 0.39, CYN - 0.01, cx - 0.05, CYN + 0.33)
R("metal3", cx - 0.37, CYN - 0.01, cx - 0.07, 10.76)

cx = MR_CX                                                     # reset switch
d_pad(cx, half=0.175)
R("via2", cx - 0.535, CYN + 0.02, cx - 0.255, CYN + 0.30)
R("metal3", cx - 0.645, CYN - 0.09, cx - 0.145, CYN + 0.41)
R("via3", cx - 0.555, CYN + 0.00, cx - 0.235, CYN + 0.32)
R("metal4", cx - 0.56, CYN - 0.005, cx - 0.23, CYN + 0.325)
R("metal1", cx + 0.235, CYN - 0.03, cx + 0.555, CYN + 0.35)
R("via1", cx + 0.265, CYN + 0.03, cx + 0.525, CYN + 0.29)
R("metal2", cx + 0.205, CYN - 0.03, cx + 0.585, CYN + 0.35)
R("metal1", cx - 0.23, CYN - 0.65, cx + 0.23, CYN - 0.215)
R("via1", cx - 0.13, CYN - 0.60, cx + 0.13, CYN - 0.34)
R("metal2", cx - 0.19, CYN - 0.63, cx + 0.19, CYN - 0.31)
label("VB", "metal2", cx + 0.395, CYN + 0.16)
label("RST", "metal2", cx, CYN - 0.47)

# ------------------------------------------------------------ PFET row
bbp = parse(CELLS / f"{devmap['MP']}.mag")["bbox"]
nw_half = -bbp[0] + 0.265
CX_MP, CYP_MP = nw_half, 12.05
CX_MIP, CYP_MIP = MIN_CX, 10.55
place("MP", "MP", CX_MP, CYP_MP)
place("MIP", "MIP", CX_MIP, CYP_MIP)
strips = [CX_MP + (j - NF / 2) * 0.48 for j in range(NF + 1)]
for x in strips[0::2]:
    R("metal1", x - 0.115, CYP_MP + 2.15, x + 0.115, CYP_MP + 2.56)
R("metal1", strips[0] - 0.115, CYP_MP + 2.54, strips[-1] + 0.115, CYP_MP + 2.77)   # VDD bar over all fingers
for x in strips[1::2]:
    R("metal1", x - 0.16, CYP_MP - 1.63, x + 0.16, CYP_MP - 1.25)
    R("via1", x - 0.13, CYP_MP - 1.57, x + 0.13, CYP_MP - 1.31)
R("metal2", strips[1] - 0.18, CYP_MP - 1.60, strips[-2] + 0.18, CYP_MP - 1.28)
XS = CX_MP + 0.405
R("metal2", XS, 8.30, XS + 0.26, CYP_MP - 1.28)                # bus -> load drain strap
R("metal1", strips[0] + 0.095, CYP_MP - 2.255, strips[-1] - 0.095, CYP_MP - 2.025)
XG = CX_MP - 0.045                                             # FG stack on the gate bar
R("metal1", XG - 0.20, CYP_MP - 2.38, XG + 0.20, CYP_MP - 1.97)
R("via1", XG - 0.13, CYP_MP - 2.305, XG + 0.13, CYP_MP - 2.045)
R("metal2", XG - 0.19, CYP_MP - 2.35, XG + 0.19, CYP_MP - 2.0)
R("via2", XG - 0.14, CYP_MP - 2.315, XG + 0.14, CYP_MP - 2.035)
R("metal3", XG - 0.25, CYP_MP - 2.425, XG + 0.25, CYP_MP - 1.925)
R("via3", XG - 0.16, CYP_MP - 2.335, XG + 0.16, CYP_MP - 2.015)
R("metal4", XG - 0.165, CYP_MP - 2.34, XG + 0.165, CYP_MP - 2.01)
R("metal4", XG - 0.20, 5.15, XG + 0.20, CYP_MP - 2.0)          # FG trunk (starts on the top-plate bar)
R("metal4", XG - 0.20, CYN - 0.005, MR_CX - 0.23, CYN + 0.325) # trunk -> reset-switch drain
label("FG", "metal4", XG, 7.0)

R("metal1", CX_MIP + 0.105, CYP_MIP + 0.65, CX_MIP + 0.335, CYP_MIP + 1.06)
x = CX_MIP - 0.22
R("metal1", x - 0.16, CYP_MIP - 0.15, x + 0.16, CYP_MIP + 0.23)
R("via1", x - 0.13, CYP_MIP - 0.09, x + 0.13, CYP_MIP + 0.17)
R("metal2", x - 0.19, CYP_MIP - 0.12, x + 0.19, CYP_MIP + 0.20)
R("via2", x - 0.14, CYP_MIP - 0.10, x + 0.14, CYP_MIP + 0.18)
R("metal3", x - 0.17, CYP_MIP - 0.13, x + 0.17, CYP_MIP + 0.21)
R("metal1", CX_MIP - 0.145, CYP_MIP - 0.95, CX_MIP + 0.48, CYP_MIP - 0.525)
R("via1", CX_MIP + 0.17, CYP_MIP - 0.90, CX_MIP + 0.43, CYP_MIP - 0.64)
R("metal2", CX_MIP + 0.14, CYP_MIP - 0.93, CX_MIP + 0.48, CYP_MIP - 0.58)
label("Y", "metal3", CX_MIP - 0.22, 9.5)
label("YB", "metal2", pd_cx[0] + 1.0, 8.43)
R("metal1", CX_MIP + 0.30, CYP_MIP + 1.04, CX_MIP + 0.53, CYP_MP + 2.77)   # VDD
R("metal1", CX_MP - 0.40, CYP_MP + 2.54, CX_MIP + 0.53, CYP_MP + 2.77)
label("VDD", "metal1", CX_MP + 1.0, CYP_MP + 2.655)
label("VSS", "metal1", pd_cx[0] + 2.0, 8.64)

tcl = ["drc off", "snap internal", f"addpath {CELLS}", f"load {NAME} -silent", "tech unlock *"] + cmds + \
      ["drc on", f"save {NAME}", "puts GENDONE", "quit -noprompt"]
(OUT / f"{NAME}.tcl").write_text("\n".join(tcl) + "\n")
print(f"K={K} NF={NF} params={P} -> {OUT/(NAME+'.tcl')} ({len(cmds)} cmds)")
