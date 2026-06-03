# Sky130 layout: Magic cell + KLayout DRC + ngspice post-layout

Analog **FGMOS–RTL** macro in Magic; **pad frame + GPIO harness** in LibreLane.

## Prerequisites

| Tool | Purpose |
|------|---------|
| [sky130A PDK](https://github.com/google/skywater-pdk) | `PDK_ROOT`, Magic tech `sky130A` |
| [Magic](http://opencircuitdesign.com/magic/) | Custom cell layout, extraction |
| [KLayout](https://www.klayout.de/) | Batch DRC on exported GDS |
| [ngspice](https://ngspice.sourceforge.io/) | Post-layout BSIM simulation |
| [LibreLane](https://github.com/librelane/librelane) | Digital wrapper, STA |

```bash
export PDK_ROOT=$HOME/share/pdk
export PDK=sky130A
source layout/setup_pdk.sh
```

## Post-layout simulation flow (no silicon required)

```bash
make -C layout magic          # automated macro layout → export/fgmos_rtl_cell.gds
make -C layout magic-extract  # Magic RC extract → export/fgmos_rtl_cell_extracted.spice
make -C layout klayout-drc    # KLayout DRC report → data/klayout_drc_fgmos.txt
cd .. && python sim/postlayout_signoff.py   # ngspice R_eff sweep → data/postlayout_*.csv
python sim/signoff_analysis.py              # updates tables/table_signoff_delay_energy.tex
```

## Paper figure (OpenLane fabrication view)

```bash
make -C layout openlane-figure
```

Output: `figures/fig8_openlane_fabric.pdf`.

## Directory map

```
layout/
├── magic/           # fgmos_rtl_cell layout + extract scripts
├── klayout/         # run_drc.sh
├── openlane/        # digital wrapper
└── librelane/
```
