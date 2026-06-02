# Sky130 layout: Magic cell + OpenLane digital wrapper

Analog **FGMOS–RTL** core in Magic; **pad frame + GPIO harness** in LibreLane (`~/projects/librelane`).

## Prerequisites

| Tool | Purpose |
|------|---------|
| [sky130A PDK](https://github.com/google/skywater-pdk) | `PDK_ROOT`, Magic tech `sky130A` |
| [Magic](http://opencircuitdesign.com/magic/) | Custom cell layout, DRC, GDS export |
| [LibreLane](https://github.com/librelane/librelane) | Digital wrapper, STA, Magic/Netgen extraction |
| Python `gdstk` | Render merged GDS for paper figure |

```bash
export PDK_ROOT=$HOME/share/pdk
export PDK=sky130A
export STD_CELL_LIBRARY=sky130_fd_sc_hd
```

## Paper figure (OpenLane fabrication view)

```bash
cd /path/to/fgmos_rtl
./env/bin/pip install gdstk
make -C layout openlane-figure
```

Output: `figures/fig8_openlane_fabric.pdf` (used in `article.tex`).

After a real OpenLane run, point to merged GDS:

```bash
export OPENLANE_GDS=layout/openlane/runs/<RUN_ID>/final/gds/design.gds
make -C layout openlane-figure
```

## Flow

```bash
make -C layout magic              # Magic → export/fgmos_rtl_cell.gds
make -C layout openlane-prepare   # copy GDS/LEF → macros/
layout/openlane/run_openlane.sh   # OpenLane 2
make -C layout openlane-figure    # render merged GDS for paper
```

## Directory map

```
layout/
├── magic/
├── openlane/fgmos_rtl_wrapper/
├── scripts/render_openlane_figure.py
└── xschem/
```
