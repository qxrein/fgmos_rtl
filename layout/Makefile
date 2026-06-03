# Layout flow — Magic + OpenLane wrapper
ROOT := $(abspath ..)
FIG := $(ROOT)/figures
CAS_FIG := $(ROOT)/els-cas-templates/figures
PDK ?= sky130A
PYTHON := $(abspath ../env/bin/python)

.PHONY: all openlane-figure magic magic-extract klayout-drc openlane-prepare clean

all: openlane-figure

# Paper figure: GDS layout from OpenLane run (or config preview)
openlane-figure:
	@test -x $(PYTHON) || (cd .. && python3 -m venv env && ./env/bin/pip install -r requirements.txt)
	$(PYTHON) scripts/render_openlane_figure.py
	@mkdir -p $(FIG) $(CAS_FIG)
	@cp $(FIG)/fig8_openlane_fabric.pdf $(FIG)/fig8_openlane_fabric.png $(CAS_FIG)/ 2>/dev/null || true

magic:
	@test -n "$$PDK_ROOT" || (echo "Set PDK_ROOT to sky130A install" && exit 1)
	cd magic && ./run_magic_layout.sh

magic-extract: magic
	@test -n "$$PDK_ROOT" || (echo "Set PDK_ROOT to sky130A install" && exit 1)
	cd magic && ./run_magic_extract.sh

klayout-drc: magic
	bash klayout/run_drc.sh

openlane-prepare: magic
	@mkdir -p openlane/fgmos_rtl_wrapper/macros
	cp -f magic/export/fgmos_rtl_cell.gds magic/export/fgmos_rtl_cell.lef \
	      openlane/fgmos_rtl_wrapper/macros/ 2>/dev/null || \
	  echo "Run 'make magic' first to populate macros/"

clean:
	rm -f magic/export/*.gds magic/export/*.lef magic/export/*.mag
	rm -f $(FIG)/fig8_openlane_fabric.* $(FIG)/fig8_layout_floorplan.*
	rm -f openlane/fgmos_rtl_wrapper/preview/*.gds
