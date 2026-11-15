#!/usr/bin/env python3
"""
Render OpenLane fabrication output for the paper (fig8_openlane_fabric).

Uses merged GDS from an OpenLane 2 run when present:
  layout/openlane/runs/**/final/gds/*.gds
  layout/openlane/runs/**/*merged*.gds
  or OPENLANE_GDS=/path/to/file.gds

If no GDS exists yet, builds a die/macro preview from config.json (same die size
and macro placement as the OpenLane job) so the figure path is stable until you
run the real flow.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures"
DESIGN = ROOT / "layout" / "librelane" / "fgmos_rtl_wrapper"
OLD_DESIGN = ROOT / "layout" / "openlane" / "fgmos_rtl_wrapper"
PREVIEW_GDS = DESIGN / "preview" / "fgmos_rtl_wrapper_preview.gds"

FIG_STEM = "fig8_openlane_fabric"
# Paper overview: die/core + upper metals (skip full FEOL polygon flood)
FIG_LAYERS = {68, 67, 64, 61, 48, 46, 41, 40, 39, 38, 235}
MAX_POLYGONS = 80_000


def _find_gds() -> Path | None:
    env = os.environ.get("OPENLANE_GDS")
    if env and Path(env).is_file():
        return Path(env)
    patterns = [
        ROOT / "layout" / "librelane" / "fgmos_rtl_wrapper" / "runs",
        ROOT / "layout" / "openlane" / "runs",
        DESIGN / "runs",
        Path.home() / "projects" / "librelane",
    ]
    candidates: list[Path] = []
    for base in patterns:
        if not base.exists():
            continue
        candidates.extend(base.rglob("*.gds"))
        candidates.extend(base.rglob("*.gds.gz"))
    # Prefer LibreLane final GDS
    ranked = sorted(candidates, key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True)
    for key in ("final/gds", "merged", "final", "gdsii", "fgmos_rtl_wrapper"):
        for p in ranked:
            if key in str(p).lower() and "spm" not in str(p).lower():
                return p
    for p in ranked:
        if "fgmos_rtl_wrapper" in str(p) and p.suffix == ".gds":
            return p
    return ranked[0] if ranked else None


def _parse_die_area_um() -> tuple[float, float]:
    import re

    cfg = DESIGN / "config.yaml"
    if not cfg.is_file():
        cfg = OLD_DESIGN / "config.json"
    area_str = "0 0 500 500"
    if cfg.is_file():
        text = cfg.read_text()
        if cfg.suffix == ".json":
            data = json.loads(text)
            area_str = data.get("DIE_AREA", area_str)
        else:
            m = re.search(r'DIE_AREA:\s*["\']?([^"\']+)["\']?', text)
            if m:
                area_str = m.group(1)
    parts = [float(x) for x in area_str.split()]
    if len(parts) == 4:
        return parts[2] - parts[0], parts[3] - parts[1]
    return 500.0, 500.0


def _macro_rect_um() -> tuple[float, float, float, float]:
    mp = DESIGN / "macro_placement.cfg"
    if mp.is_file():
        for line in mp.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            toks = line.split()
            if len(toks) >= 4 and toks[0] == "u_fgmos":
                x, y = float(toks[1]), float(toks[2])
                # Typical macro ~50 um — match config die scale
                w, h = 50.0, 50.0
                return x, y, x + w, y + h
    return 90.0, 90.0, 140.0, 140.0


def _write_preview_gds(path: Path) -> Path:
    import gdstk

    w_um, h_um = _parse_die_area_um()
    x0, y0, x1, y1 = _macro_rect_um()
    path.parent.mkdir(parents=True, exist_ok=True)

    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    top = lib.new_cell("fgmos_rtl_wrapper")

    # Layer map (Sky130-ish visualization only)
    top.add(gdstk.rectangle((0, 0), (w_um, h_um), layer=68, datatype=20))  # seal / boundary
    top.add(gdstk.rectangle((x0, y0), (x1, y1), layer=68, datatype=16))    # macro block
    top.add(gdstk.rectangle((5, 5), (w_um - 5, h_um - 5), layer=235, datatype=0))  # core area

    lib.write_gds(str(path))
    return path


def _polygons_from_gds(gds_path: Path) -> tuple[list[tuple[int, int, np.ndarray]], float]:
    """Return polygon list and a scale factor to convert coordinates to µm."""
    import gdstk

    lib = gdstk.read_gds(str(gds_path))
    top = lib.top_level()[0] if lib.top_level() else lib.cells[0]

    # gdstk returns coordinates in library units.
    # Determine the scale so that 1 plot-unit = 1 µm:
    #   lib.unit is metres-per-user-unit (e.g. 1e-6 for µm-native, 1e-9 for nm-native)
    scale_to_um = lib.unit / 1e-6  # = 1.0 if unit is µm, 0.001 if unit is nm

    out: list[tuple[int, int, np.ndarray]] = []
    for poly in top.get_polygons():
        layer = poly.layer
        if layer not in FIG_LAYERS:
            continue
        pts = np.asarray(poly.points) * scale_to_um   # now in µm
        if len(pts) >= 3:
            out.append((layer, poly.datatype, pts))
    if len(out) > MAX_POLYGONS:
        rng = np.random.default_rng(0)
        idx = rng.choice(len(out), size=MAX_POLYGONS, replace=False)
        out = [out[i] for i in sorted(idx)]
    return out, scale_to_um


def _layer_color(layer: int) -> str:
    palette = {
        68: "#c62828",
        235: "#1565c0",
        67: "#2e7d32",
        64: "#f9a825",
        61: "#6a1b9a",
    }
    return palette.get(layer, "#78909c")


def render(gds_path: Path, source_note: str) -> None:
    polys, _scale = _polygons_from_gds(gds_path)
    if not polys:
        raise RuntimeError(f"No polygons in {gds_path}")

    fig, ax = plt.subplots(figsize=(3.5, 3.5))
    for layer, _dtype, pts in polys:
        ax.fill(
            pts[:, 0], pts[:, 1],
            facecolor=_layer_color(layer),
            edgecolor="#263238",
            linewidth=0.15,
            alpha=0.75,
        )

    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(r"Position ($\mu$m)")
    ax.set_ylabel(r"Position ($\mu$m)")
    ax.set_title("LibreLane fabrication view (sky130)", fontsize=8)
    ax.tick_params(labelsize=6)
    fig.text(
        0.5, 0.01, source_note,
        ha="center", fontsize=5.5, style="italic", transform=fig.transFigure,
    )
    fig.tight_layout(rect=[0, 0.04, 1, 1])

    OUT.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        p = OUT / f"{FIG_STEM}.{ext}"
        fig.savefig(p, dpi=300, bbox_inches="tight", pad_inches=0.05)
        print(f"  wrote {p}")

    cas = ROOT / "els-cas-templates" / "figures"
    if cas.parent.exists():
        cas.mkdir(parents=True, exist_ok=True)
        for ext in ("pdf", "png"):
            shutil.copy2(OUT / f"{FIG_STEM}.{ext}", cas / f"{FIG_STEM}.{ext}")

    plt.close(fig)


def main() -> None:
    gds = _find_gds()
    if gds is not None:
        note = f"Source: {gds.relative_to(ROOT) if gds.is_relative_to(ROOT) else gds.name}"
        print(f"  rendering OpenLane GDS: {gds}")
        render(gds, note)
        return

    print("  no OpenLane GDS found — writing preview from config.json + macro_placement.cfg")
    try:
        import gdstk  # noqa: F401
    except ImportError:
        raise SystemExit("Install gdstk: ./env/bin/pip install gdstk") from None

    preview = _write_preview_gds(PREVIEW_GDS)
    render(preview, "Preview layout (run OpenLane to replace with merged.gds)")


if __name__ == "__main__":
    main()
