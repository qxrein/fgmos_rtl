"""
v2 QFG threshold-logic cell layout generator (Sky130A, Magic).

Floorplan (um, y up):
  y 0.00-2.95   ballast MIM  CBL (FG / VSS)
  y 4.15-6.55   input MIMs   CA, CB, CC (FG / A,B,C)          [>=1.2 um plate gaps: capm halo rule]
  y ~7.0-8.8    NFET row     MNA | MR | MNB | MIN | MNC       (gates contacted at the bottom)
  y ~9.1-14.8   PFET row     MP (nf=4, 4x4um)  ...  MIP
Routing: m1 device-local + rails, m2 YB bus / pins, m3 input fingers + Y jumper, m4 FG trunk.

Writes layout/v2/magic/qfg_tlg.tcl (run with Magic) which builds cell `qfg_tlg`.
"""
from pathlib import Path

from magparse import parse

HERE = Path(__file__).resolve().parent
CELLS = HERE / "cells"
OUT = HERE / "magic"
OUT.mkdir(exist_ok=True)
devmap = dict(l.split() for l in open(CELLS / "devmap.txt"))

cmds = []


def R(layer, x1, y1, x2, y2):
    cmds.append(f"box values {x1:.3f}um {y1:.3f}um {x2:.3f}um {y2:.3f}um; paint {layer}")


def place(kind, inst, cx, cy):
    cell = devmap[kind]
    bb = parse(CELLS / f"{cell}.mag")["bbox"]
    # getcell aligns the child's lower-left (FIXED_BBOX) with the box lower-left
    llx, lly = cx + bb[0], cy + bb[1]
    cmds.append(f"box values {llx:.3f}um {lly:.3f}um {llx:.3f}um {lly:.3f}um")
    cmds.append(f"getcell {cell}")
    cmds.append(f"identify {inst}")


def label(text, layer, x, y, port=None):
    cmds.append(f"box values {x:.3f}um {y:.3f}um {x:.3f}um {y:.3f}um")
    cmds.append(f"label {text} c {layer}")
    if port is not None:
        cmds.append(f"port make {port}")


# ---------------------------------------------------------------- capacitors
def mim(x0, y0, w, l, ml=0.2, mr=0.2, mb=0.2, mt=0.2):
    """MIM (cap_mim_m3_1): capm w x l at (x0,y0). The m3 bottom plate is ONE rectangle that
    encloses the capm (margins ml/mr/mb/mt) so that every bottom-plate via sits inside it
    (Magic capm.11 halo: no other metal3 within 1.34 um). Contact = capm-0.2; m4 = contact+0.01."""
    R("metal3", x0 - ml, y0 - mb, x0 + w + mr, y0 + l + mt)
    R("mimcap", x0, y0, x0 + w, y0 + l)
    R("mimcapcontact", x0 + 0.2, y0 + 0.2, x0 + w - 0.2, y0 + l - 0.2)
    R("metal4", x0 + 0.19, y0 + 0.19, x0 + w - 0.19, y0 + l - 0.19)


mim(0.2, 0.2, 9.2, 2.55, ml=1.0)  # CBL  (ballast, bottom plate = VSS; wide left margin for the VSS via)
for i in range(3):                  # CA, CB, CC (2 x 2 um); 0.75 um top margin hosts the input via2
    mim(0.2 + 3.6 * i, 4.35, 2.0, 2.0, mt=0.75)
# FG trunk links between the input-cap top plates and the ballast top plate (m4)
for xc in (1.2, 4.8, 8.4):
    R("metal4", xc - 0.2, 2.45, xc + 0.2, 4.65)

# ballast bottom plate -> VSS: m3 tab, via2, m2 lane up the left edge
R("via2", -0.66, 0.46, -0.38, 0.74)
R("metal2", -0.72, 0.40, -0.32, 0.80)
R("metal2", -0.66, 0.40, -0.38, 8.80)

# ---------------------------------------------------------------- NFET row
CYN = 7.80
row = [("MN", "MNA", 0.90), ("MR", "MR", 2.655), ("MN", "MNB", 4.41), ("MN", "MIN", 5.99), ("MN", "MNC", 7.57)]
for kind, inst, cx in row:
    place(kind, inst, cx, CYN)

# VSS rail over the shared top tap bars, extended left to the VSS lane
R("metal1", -0.72, 8.525, 8.36, 8.755)
R("metal1", -0.72, 8.48, -0.32, 8.80)
R("via1", -0.65, 8.51, -0.39, 8.77)
R("metal2", -0.72, 8.48, -0.32, 8.83)

YB_BUS = (0.45, 8.30, 7.58, 8.56)
R("metal2", *YB_BUS)


def nfet_gate_landing(cx, stack_to_m3=False):
    y = CYN
    R("metal1", cx - 0.145, y - 0.65, cx + 0.48, y - 0.215)
    R("via1", cx + 0.16, y - 0.60, cx + 0.42, y - 0.34)
    R("metal2", cx + 0.06, y - 0.66, cx + 0.52, y - 0.28)
    if stack_to_m3:
        R("via2", cx + 0.15, y - 0.61, cx + 0.43, y - 0.33)
        R("metal3", cx + 0.10, y - 0.66, cx + 0.48, y - 0.28)


def d_pad(cx, half=0.0, to_bus=False):
    """via1 landing on the left (D) strip; half = extra offset for the MR geometry."""
    y = CYN
    x1, x2 = cx - 0.38 - half, cx - 0.06 - half
    R("metal1", x1, y - 0.03, x2, y + 0.35)
    R("via1", x1 + 0.03, y + 0.03, x2 - 0.03, y + 0.29)
    R("metal2", x1 - 0.03, y - 0.03, x2 + 0.03, y + (0.76 if to_bus else 0.35))


def s_to_vss(cx):
    R("metal1", cx + 0.105, CYN + 0.30, cx + 0.335, CYN + 0.75)


# input pull-downs A, B, C: gate stack to m3 + finger down to the plate; drain to YB bus
for (_, inst, cx), plate_x0 in zip([row[0], row[2], row[4]], (0.0, 3.6, 7.2)):
    nfet_gate_landing(cx)
    R("via2", cx + 0.15, 6.57, cx + 0.43, 6.85)                 # in plate top margin (capm.11: m2 >= 0.14 from capm)
    R("metal2", cx + 0.10, 6.52, cx + 0.48, 6.90)
    R("metal2", cx + 0.16, 6.52, cx + 0.42, CYN - 0.30)
    d_pad(cx, to_bus=True)
    s_to_vss(cx)
for net, (_, _, cx) in zip("ABC", [row[0], row[2], row[4]]):
    label(net, "metal3", cx + 0.29, 6.95)

# MIN (inverter n): gate = YB (vertical to bus and on to MIP gate), drain = Y, source = VSS
cx = row[3][2]
nfet_gate_landing(cx)
d_pad(cx)
s_to_vss(cx)
R("metal2", cx + 0.16, CYN - 0.66, cx + 0.42, 9.97)        # YB vertical (MIN gate -> bus -> MIP gate)
# Y jumper on m3 (crosses the YB bus)
R("via2", cx - 0.36, CYN + 0.02, cx - 0.08, CYN + 0.30)
R("metal3", cx - 0.39, CYN - 0.01, cx - 0.05, CYN + 0.33)
R("metal3", cx - 0.37, CYN - 0.01, cx - 0.07, 10.76)

# MR (reset switch): D = FG (stack to m4), S = VB pin, G = RST pin
cx = row[1][2]
d_pad(cx, half=0.175)
R("via2", cx - 0.535, CYN + 0.02, cx - 0.255, CYN + 0.30)
R("metal3", cx - 0.645, CYN - 0.09, cx - 0.145, CYN + 0.41)
R("via3", cx - 0.555, CYN + 0.00, cx - 0.235, CYN + 0.32)
R("metal4", cx - 0.56, CYN - 0.005, cx - 0.23, CYN + 0.325)
R("metal1", cx + 0.235, CYN - 0.03, cx + 0.555, CYN + 0.35)   # VB pad
R("via1", cx + 0.265, CYN + 0.03, cx + 0.525, CYN + 0.29)
R("metal2", cx + 0.205, CYN - 0.03, cx + 0.585, CYN + 0.35)
R("metal1", cx - 0.23, CYN - 0.65, cx + 0.23, CYN - 0.215)   # RST landing
R("via1", cx - 0.13, CYN - 0.60, cx + 0.13, CYN - 0.34)
R("metal2", cx - 0.19, CYN - 0.63, cx + 0.19, CYN - 0.31)
label("VB", "metal2", cx + 0.395, CYN + 0.16)
label("RST", "metal2", cx, CYN - 0.47)

# ---------------------------------------------------------------- PFET row
CYP_MP, CX_MP = 12.05, 1.795
CYP_MIP, CX_MIP = 10.55, 5.99
place("MP", "MP", CX_MP, CYP_MP)
place("MIP", "MIP", CX_MIP, CYP_MIP)

strips = [CX_MP + d for d in (-0.96, -0.48, 0.0, 0.48, 0.96)]
for x in (strips[0], strips[2], strips[4]):                 # VDD strips up to the top tap bar
    R("metal1", x - 0.115, CYP_MP + 2.15, x + 0.115, CYP_MP + 2.56)
for x in (strips[1], strips[3]):                            # YB strips: via1 + m2 strap
    R("metal1", x - 0.16, CYP_MP - 1.63, x + 0.16, CYP_MP - 1.25)
    R("via1", x - 0.13, CYP_MP - 1.57, x + 0.13, CYP_MP - 1.31)
R("metal2", strips[1] - 0.18, CYP_MP - 1.60, strips[3] + 0.18, CYP_MP - 1.28)
R("metal2", 2.20, YB_BUS[1], 2.46, CYP_MP - 1.28)          # bus -> MP drain strap
# MP gate bar + FG stack (via1/via2/via3) to the m4 trunk
R("metal1", strips[0] + 0.095, CYP_MP - 2.255, strips[4] - 0.095, CYP_MP - 2.025)
R("metal1", 1.55, CYP_MP - 2.38, 1.95, CYP_MP - 1.97)
R("via1", 1.62, CYP_MP - 2.305, 1.88, CYP_MP - 2.045)
R("metal2", 1.56, CYP_MP - 2.35, 1.94, CYP_MP - 2.0)
R("via2", 1.61, CYP_MP - 2.315, 1.89, CYP_MP - 2.035)
R("metal3", 1.50, CYP_MP - 2.425, 2.00, CYP_MP - 1.925)
R("via3", 1.59, CYP_MP - 2.335, 1.91, CYP_MP - 2.015)
R("metal4", 1.585, CYP_MP - 2.34, 1.915, CYP_MP - 2.01)
# FG trunk on m4: cap top plates -> MR drain -> MP gate
R("metal4", 1.55, 6.00, 1.95, CYP_MP - 2.0)
R("metal4", 1.55, CYN - 0.005, 2.45, CYN + 0.325)
label("FG", "metal4", 1.75, 7.0)

# MIP: S -> VDD tap bar, D -> Y (m3 jumper), G -> YB
R("metal1", CX_MIP + 0.105, CYP_MIP + 0.65, CX_MIP + 0.335, CYP_MIP + 1.06)
x = CX_MIP - 0.22
R("metal1", x - 0.16, CYP_MIP - 0.15, x + 0.16, CYP_MIP + 0.23)
R("via1", x - 0.13, CYP_MIP - 0.09, x + 0.13, CYP_MIP + 0.17)
R("metal2", x - 0.19, CYP_MIP - 0.12, x + 0.19, CYP_MIP + 0.20)
R("via2", x - 0.14, CYP_MIP - 0.10, x + 0.14, CYP_MIP + 0.18)
R("metal3", x - 0.17, CYP_MIP - 0.13, x + 0.17, CYP_MIP + 0.21)
R("metal1", CX_MIP - 0.145, CYP_MIP - 0.95, CX_MIP + 0.48, CYP_MIP - 0.525)  # gate landing
R("via1", CX_MIP + 0.17, CYP_MIP - 0.90, CX_MIP + 0.43, CYP_MIP - 0.64)
R("metal2", CX_MIP + 0.14, CYP_MIP - 0.93, CX_MIP + 0.48, CYP_MIP - 0.58)
label("Y", "metal3", CX_MIP - 0.22, 9.5)
label("YB", "metal2", 3.5, 8.43)

# VDD: MIP tap bar -> MP tap bar (m1)
R("metal1", CX_MIP + 0.30, CYP_MIP + 1.04, CX_MIP + 0.53, CYP_MP + 2.77)
R("metal1", CX_MP - 0.40, CYP_MP + 2.54, CX_MIP + 0.53, CYP_MP + 2.77)
label("VDD", "metal1", 4.5, CYP_MP + 2.655)
label("VSS", "metal1", 4.0, 8.64)

# ---------------------------------------------------------------- emit
tcl = ["# auto-generated by gen_layout.py", "drc off", "snap internal",
       f"addpath {CELLS}", "load qfg_tlg -silent", "tech unlock *"]
tcl += cmds
tcl += ["select top cell", "port renumber" if False else "", "drc on", "save qfg_tlg", "puts GENDONE", "quit -noprompt"]
(OUT / "qfg_tlg.tcl").write_text("\n".join(tcl) + "\n")
print(f"wrote {OUT/'qfg_tlg.tcl'} with {len(cmds)} commands")
