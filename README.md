# FGMOS RTL Fabric — Simulation Suite

Complete, publication-ready simulation package for the FGMOS-based RTL reconfigurable logic fabric paper.

## Quick Start

```bash
# Fish shell: use run_sim.fish (do NOT source env/bin/activate)
./run_sim.fish

# Bash/zsh:
./run_sim.sh

# Or without activate (any shell):
python3 -m venv env
./env/bin/pip install -r requirements.txt
./env/bin/python sim/main.py

# Optional: run SPICE simulations (requires ngspice)
bash spice/run_all_spice.sh
```

## Project Structure

```
fgmos_rtl/
├── spice/          # ngspice netlists (Sky130 primitives)
├── sim/            # Python behavioral simulations
├── figures/        # Generated PDF+PNG (Overleaf-ready)
├── tables/         # LaTeX .tex table snippets
├── data/           # Raw CSV simulation output
└── requirements.txt
```

## Three Core Claims

1. **Claim 1**: FGMOS in ohmic region provides >10x programmable resistance range via Vctrl
2. **Claim 2**: Single RTL cell implements NOR, MAJ, AND by Vctrl alone (no rewiring)
3. **Claim 3**: Partial floating-gate charge creates CMOS-native p-bit (no MTJ/exotic materials)
4. **Sign-off**: PVT (TT/SS/FF), mismatch MC, delay/energy/area vs conventional RTL and CMOS

## Key Physics

- FGMOS operates in **ohmic/triode** region (NOT saturation — this is the core novelty)
- Vds < (Vfg_eff - Vth0) enforced in every simulation call
- All capacitances within Sky130 MIM range (1–100 fF)
- Sky130 tt-corner: Vth0=0.49V, kn=270μA/V², Vcc=1.8V

## Layout (Magic + OpenLane)

```bash
make -C layout openlane-figure   # fig8 OpenLane GDS render (paper)
make -C layout magic             # requires PDK_ROOT + Magic
# see layout/README.md for OpenLane wrapper
```

## Paper (Elsevier CAS)

The journal manuscript is self-contained in [`els-cas-templates/`](els-cas-templates/) (figures copied into `els-cas-templates/figures/`):

```bash
python sim/main.py
make -C els-cas-templates    # requires pdflatex + bibtex
```

Main file: `els-cas-templates/article.tex`. See [els-cas-templates/README.md](els-cas-templates/README.md).

## Overleaf Integration

See [overleaf_import_guide.md](overleaf_import_guide.md) for standalone figure/table paths, or use the full CAS manuscript above.

## Technology

- **Process**: SkyWater Sky130 (130nm, open-source PDK)
- **Simulation**: Python behavioral + ngspice SPICE verification
- **No paid tools required** — fully reproducible with free/open-source stack

## Toolchain

- Python 3.8+ with numpy, scipy, matplotlib, pandas, schemdraw
- ngspice (optional, for SPICE-level verification)
- Overleaf (free tier) for LaTeX compilation
