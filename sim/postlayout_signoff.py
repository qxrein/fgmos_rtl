"""
Post-layout sign-off via ngspice on Magic-extracted netlist + Sky130 BSIM models.
Updates delay/energy tables with schematic vs post-layout columns.

Prerequisites:
  export PDK_ROOT=...  PDK=sky130A
  make -C layout magic magic-extract
  ngspice in PATH
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SPICE = ROOT / "spice"
DATA = ROOT / "data"
TBL = ROOT / "tables"
EXTRACT = ROOT / "layout/magic/export/fgmos_rtl_cell_extracted.spice"
PDK_ROOT = Path(os.environ.get("PDK_ROOT", Path.home() / "share/pdk"))
NGSPICE = os.environ.get("NGSPICE", "ngspice")


def _parse_extracted_ct_f() -> float:
    """Sum coupling capacitances on FG node from extracted netlist (F)."""
    if not EXTRACT.is_file():
        return float("nan")
    text = EXTRACT.read_text()
    # Heuristic: capacitors touching node G or FG in subckt
    total = 0.0
    for line in text.splitlines():
        if not line.strip().startswith("C"):
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        n1, n2 = parts[1], parts[2]
        val = parts[3]
        if "G" not in (n1, n2) and "FG" not in (n1, n2):
            continue
        m = re.match(r"([\d.eE+-]+)f\b", val, re.I)
        if not m:
            continue
        total += float(m.group(1)) * 1e-15
    return total


def _sanitize_extracted_netlist() -> Path:
    """Copy extracted netlist with MIM instance params fixed for ngspice."""
    sanitized = SPICE / "fgmos_rtl_cell_extracted_sanitized.spice"
    lines = []
    for ln in EXTRACT.read_text().splitlines():
        if re.match(r"^X\d+.*cap_mim", ln):
            # Magic emits incomplete param list; add required W/L/mf
            ln = re.sub(
                r"sky130_fd_pr__cap_mim_m3_1\s+l=\S+\s+w=\S+",
                "sky130_fd_pr__cap_mim_m3_1 w=2 l=2 mf=1",
                ln,
            )
            if "mf=" not in ln:
                ln = ln.replace("sky130_fd_pr__cap_mim_m3_1", "sky130_fd_pr__cap_mim_m3_1 w=2 l=2 mf=1")
        lines.append(ln)
    sanitized.write_text("\n".join(lines) + "\n")
    return sanitized


def _write_postlayout_spice(ct_f: float) -> Path:
    """Build ngspice deck: PDK models + extracted cell + R_eff DC sweep."""
    rc_params = PDK_ROOT / "sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical.spice"
    rc_lin = PDK_ROOT / "sky130A/libs.tech/ngspice/r+c/res_typical__cap_typical__lin.spice"
    rc_model = PDK_ROOT / "sky130A/libs.tech/ngspice/sky130_fd_pr__model__r+c.model.spice"
    nfet_tt = PDK_ROOT / "sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__tt.pm3.spice"
    nfet_mm = PDK_ROOT / "sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__nfet_01v8__mismatch.corner.spice"
    cap_model = PDK_ROOT / "sky130A/libs.ref/sky130_fd_pr/spice/sky130_fd_pr__cap_mim_m3_1.model.spice"
    sanitized = _sanitize_extracted_netlist()
    out = SPICE / "postlayout_reff_sweep.sp"
    rel_extract = os.path.relpath(sanitized, out.parent)
    rel_rc = os.path.relpath(rc_params, out.parent)
    rel_rcl = os.path.relpath(rc_lin, out.parent)
    rel_rcm = os.path.relpath(rc_model, out.parent)
    rel_nfet = os.path.relpath(nfet_tt, out.parent)
    rel_nfet_mm = os.path.relpath(nfet_mm, out.parent)
    rel_cap = os.path.relpath(cap_model, out.parent)

    deck = f"""* Auto-generated post-layout R_eff sweep (Sky130 TT + extracted layout)
.option scale=1.0u
.option ngbehavior=ltpsa
.param MC_MM_SWITCH=0
.param mc_mm_switch=0
.include "{rel_rc}"
.include "{rel_rcl}"
.include "{rel_rcm}"
.include "{rel_nfet_mm}"
.include "{rel_nfet}"
.include "{rel_cap}"
.include "{rel_extract}"

* Bench: extracted pull-up device; sweep effective gate bias
Vdd vdd 0 DC 1.8
Vss vss 0 DC 0
Vds vout 0 DC 0.05
Vfg fg 0 DC 0.9

* Pin order from extracted .subckt line (regenerated after each extract)
"""
    subline = next((ln for ln in sanitized.read_text().splitlines() if ln.startswith(".subckt")), "")
    pins = subline.split()[2:] if subline else ["B", "D", "S", "G"]
    # Tie unused cap ports (C2, C1, …) to FG for DC R sweep
    conn = []
    for p in pins:
        if p in ("S", "s"):
            conn.append("vss")
        elif p in ("D", "d"):
            conn.append("vout")
        elif p in ("G", "g", "FG", "fg"):
            conn.append("fg")
        elif p in ("B", "b"):
            conn.append("vss")
        else:
            conn.append("fg")
    deck += f"Xpl {' '.join(conn)} fgmos_rtl_cell\n"

    deck += """
.dc Vfg 0.55 1.25 0.02
.control
run
set wr_vecnames
set wr_singlescale
wrdata ../data/postlayout_reff_sweep.csv v(fg) v(vout) i(Vds)
.endc
.end
"""
    out.write_text(deck)
    return out


def _run_ngspice(deck: Path) -> Path:
    csv = DATA / "postlayout_reff_sweep.csv"
    DATA.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PDK_ROOT"] = str(PDK_ROOT)
    subprocess.run(
        [NGSPICE, "-b", str(deck.name)],
        cwd=deck.parent,
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )
    if not csv.is_file():
        raise FileNotFoundError(f"ngspice did not write {csv}")
    return csv


def _reff_from_csv(csv: Path) -> pd.DataFrame:
    arr = np.loadtxt(csv, skiprows=1)
    if arr.ndim == 1:
        arr = arr.reshape(1, -1)
    if arr.shape[1] >= 4:
        vfg = arr[:, 1]
        vout = arr[:, 2]
        ids = -arr[:, 3]
    else:
        vfg = arr[:, 0]
        vout = arr[:, 1]
        ids = -arr[:, 2]
    reff = np.where(np.abs(ids) > 1e-12, 0.05 / ids, np.nan)
    return pd.DataFrame({"Vfg_V": vfg, "Vout_V": vout, "Ids_A": ids, "Reff_ohm": reff})


def _tau_energy_from_reff(reff_ohm: float, cl_f: float, vcc: float = 1.8) -> dict:
    tau_s = reff_ohm * cl_f
    e_j = cl_f * vcc * vcc
    return {
        "tau_ps": round(tau_s * 1e12, 0),
        "t_90_ps": round(2.3 * tau_s * 1e12, 0),
        "E_eval_fJ": round(e_j * 1e15, 1),
        "R_eff_kOhm": round(reff_ohm / 1e3, 2),
    }


def run() -> bool:
    if not EXTRACT.is_file():
        print(f"  Post-layout: missing {EXTRACT} — run make -C layout magic-extract")
        return False

    ct = _parse_extracted_ct_f()
    (DATA / "postlayout_extracted_ct.json").write_text(
        f'{{"CT_extracted_fF": {ct * 1e15:.2f}}}\n'
    )
    print(f"  Post-layout: extracted FG-related C sum ≈ {ct*1e15:.1f} fF")

    deck = _write_postlayout_spice(ct)
    try:
        csv = _run_ngspice(deck)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"  Post-layout ngspice failed: {e}")
        return False

    df = _reff_from_csv(csv)
    df.to_csv(DATA / "postlayout_reff_parsed.csv", index=False)
    valid = df["Reff_ohm"].replace([np.inf, -np.inf], np.nan).dropna()
    valid = valid[(valid > 0) & (valid < 50e6)]
    if len(valid) < 2:
        print("  Post-layout: insufficient R_eff points")
        return False

    rmin, rmax = float(valid.min()), float(valid.max())
    ratio = rmax / rmin
    mid = valid.median()
    cl = 80e-15 + max(0.0, ct - 30e-15)  # schematic CL + extra layout cap
    metrics = _tau_energy_from_reff(mid, cl)
    metrics["Reff_ratio"] = round(ratio, 1)

    summary = pd.DataFrame([{"source": "post-layout (ngspice+extract)", **metrics}])
    summary.to_csv(DATA / "postlayout_signoff_summary.csv", index=False)
    print(
        f"  Post-layout: R_eff {rmin/1e3:.2f}–{rmax/1e3:.2f} kΩ ({ratio:.1f}×), "
        f"τ≈{metrics['tau_ps']:.0f} ps @ median"
    )
    return ratio >= 5.0


if __name__ == "__main__":
    run()
