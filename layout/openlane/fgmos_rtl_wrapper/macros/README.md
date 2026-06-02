# Macro artifacts (from Magic)

After `make -C layout magic`, copy:

- `layout/magic/export/fgmos_rtl_cell.gds`
- `layout/magic/export/fgmos_rtl_cell.lef`

into this directory, then run OpenLane 2 on `fgmos_rtl_wrapper`.

Until GDS exists, OpenLane synthesis of the **wrapper** still runs; macro placement step requires valid LEF/GDS.
