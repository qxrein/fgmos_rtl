"""
Shared helpers for the v2 (PMOS quasi-floating-gate threshold-logic) study.

Every electrical number in the v2 paper comes from ngspice runs driven by this
module against the open Sky130 BSIM4 models (volare-managed PDK in .eda/pdk).
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDA = ROOT / ".eda"
PDK_ROOT = Path(os.environ.get("PDK_ROOT", EDA / "pdk"))
SKY130_LIB = PDK_ROOT / "sky130A/libs.tech/ngspice/sky130.lib.spice"
NGSPICE = os.environ.get(
    "NGSPICE", "/nix/store/8xash38paka9by07h83bb602rsjkd4kg-ngspice-45/bin/ngspice"
)
RUNS = ROOT / "sim/v2/_runs"
DATA = ROOT / "data/v2"
FIGS = ROOT / "figures/v2"
SPICE = ROOT / "spice/v2"
for d in (RUNS, DATA, FIGS, SPICE):
    d.mkdir(parents=True, exist_ok=True)

VDD = 1.8

# --------------------------------------------------------------------------
# Cell netlist (v2).  YB = pseudo-NMOS ratioed node (NOR3 / MIN3 / NAND3),
# Y = restored output after a static inverter (OR3 / MAJ3 / AND3).
# FG is a quasi-floating gate: written to VB through reset switch MR while
# RST is high (inputs held low), then left floating during evaluation.
# --------------------------------------------------------------------------
DEFAULT = dict(
    wp=16.0, lp=0.15,     # PMOS load (um)              [final design, see grid2/final_corners]
    wn=0.42, ln=0.15,     # input pull-downs (um)
    cw=2.0, cl=2.0,       # input MIM coupling cap, w x l (um)
    wr=0.42, lr=0.50,     # reset switch nfet (long L for low leakage)
    bw=9.2, bl=2.55,      # ballast MIM cap FG->VSS (sets coupling ratio; 23.5 um^2, matches layout)
    wip=1.0, win=0.42,    # restoring inverter
)


def cell_subckt(p: dict | None = None, name: str | None = None, K: int = 3) -> str:
    """K-input QFG threshold cell. Port order: I0..I{K-1} RST VB Y YB FG VDD VSS."""
    q = dict(DEFAULT)
    if p:
        q.update(p)
    name = name or ("QFG_TLG" if K == 3 else f"QFG_TLG{K}")
    ins = [f"I{i}" for i in range(K)]
    lines = [f".subckt {name} {' '.join(ins)} RST VB Y YB FG VDD VSS",
             f"XMP  YB FG VDD VDD sky130_fd_pr__pfet_01v8 W={q['wp']} L={q['lp']}"]
    for i in ins:
        lines.append(f"XMN{i} YB {i} VSS VSS sky130_fd_pr__nfet_01v8 W={q['wn']} L={q['ln']}")
    for i in ins:
        lines.append(f"XC{i} FG {i} sky130_fd_pr__cap_mim_m3_1 W={q['cw']} L={q['cl']} MF=1")
    lines += [
        f"XCBL FG VSS sky130_fd_pr__cap_mim_m3_1 W={q['bw']} L={q['bl']} MF=1",
        f"XMR  FG RST VB VSS sky130_fd_pr__nfet_01v8 W={q['wr']} L={q['lr']}",
        f"XIP  Y  YB VDD VDD sky130_fd_pr__pfet_01v8 W={q['wip']} L=0.15",
        f"XIN  Y  YB VSS VSS sky130_fd_pr__nfet_01v8 W={q['win']} L=0.15",
        f".ends {name}",
    ]
    return "\n" + "\n".join(lines) + "\n"


def header(corner: str = "tt", temp: float = 27.0, mc: bool = False, seed: int | None = None) -> str:
    """PDK corner include.  NB: the Sky130 .lib sections reset mc_mm_switch=0, so the
    mismatch switch must be set AFTER the .lib line; the random seed is a parse-time option."""
    lines = ["* auto-generated", f'.lib "{SKY130_LIB}" {corner}', f".temp {temp}"]
    if mc:
        lines.append(".param mc_mm_switch=1")
        if seed is not None:
            lines.append(f".option seed={seed}")
    return "\n".join(lines) + "\n"


def run(deck: str, tag: str = "run", keep: bool = False, timeout: int = 1800) -> tuple[str, Path]:
    """Run ngspice in batch mode inside a fresh directory; return (stdout, dir)."""
    d = RUNS / f"{tag}_{uuid.uuid4().hex[:8]}"
    d.mkdir(parents=True, exist_ok=True)
    (d / "deck.sp").write_text(deck)
    r = subprocess.run(
        [NGSPICE, "-b", "deck.sp"], cwd=d, capture_output=True, text=True, timeout=timeout
    )
    out = r.stdout + r.stderr
    (d / "ngspice.log").write_text(out)
    return out, d


_meas_re = re.compile(r"^\s*([A-Za-z_][\w]*)\s*=\s*([-+0-9.eE]+)", re.M)


def parse_kv(path: Path) -> list[dict]:
    """Parse lines of 'k=v k=v ...' written by echo in .control blocks."""
    rows = []
    for ln in path.read_text().splitlines():
        kv = dict(re.findall(r"(\w+)=([-+0-9.eE]+|\S+)", ln))
        if kv:
            rows.append({k: _num(v) for k, v in kv.items()})
    return rows


def _num(v: str):
    try:
        return float(v)
    except ValueError:
        return v


PEX_NETLIST = ROOT / "layout/v2/magic/qfg_tlg_pex.spice"


def pex_cell_text(name: str = "QFG_TLG") -> str:
    """Magic-extracted (devices + parasitic C) cell wrapped to the schematic port order.
    NB: ngspice subckt names are case-insensitive, so the extracted `qfg_tlg` is renamed
    to `qfg_tlg_pex` before the `QFG_TLG` wrapper is defined."""
    txt = PEX_NETLIST.read_text().replace(".subckt qfg_tlg ", ".subckt qfg_tlg_pex ")
    return txt + f"""
.subckt {name} I0 I1 I2 RST VB Y YB FG VDD VSS
Xpl I0 I1 I2 VB RST FG Y YB VDD VSS qfg_tlg_pex
.ends {name}
"""


def pex_cell_text_k(K: int) -> str:
    """Magic-extracted K-input cell (layout/v2k/K<K>), wrapped to the schematic port order."""
    f = ROOT / f"layout/v2k/K{K}/magic/qfg_tlg_k{K}_pex.spice"
    txt = f.read_text().replace(f".subckt qfg_tlg_k{K} ", f".subckt qfg_tlg_k{K}_pex ")
    ins = " ".join(f"I{i}" for i in range(K))
    return txt + f"""
.subckt QFG_TLG{K} {ins} RST VB Y YB FG VDD VSS
Xpl {ins} VB RST FG Y YB VDD VSS qfg_tlg_k{K}_pex
.ends QFG_TLG{K}
"""
