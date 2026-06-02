# Elsevier CAS manuscript — FGMOS-RTL paper
MAIN = article
BIB  = report
FIG_SRC = ../figures
ROOT = ..

.PHONY: all figures clean

all: figures $(MAIN).pdf

# Copy simulation figures into this folder (self-contained for Overleaf)
figures:
	@mkdir -p figures
	@test -f $(FIG_SRC)/fig4_pbit_combined.pdf || (cd $(ROOT) && ./env/bin/python sim/main.py)
	cp $(FIG_SRC)/fig*.pdf $(FIG_SRC)/fig*.png figures/ 2>/dev/null || true
	@test -f figures/fig4_pbit_combined.pdf || (echo "ERROR: run: cd $(ROOT) && ./env/bin/python sim/main.py" && exit 1)
	@test -f $(FIG_SRC)/fig8_openlane_fabric.pdf || $(MAKE) -C $(ROOT)/layout openlane-figure

$(MAIN).pdf: $(MAIN).tex $(BIB).bib cas-sc.cls cas-common.sty cas-model2-names.bst figures
	pdflatex -interaction=nonstopmode $(MAIN).tex
	bibtex $(MAIN)
	pdflatex -interaction=nonstopmode $(MAIN).tex
	pdflatex -interaction=nonstopmode $(MAIN).tex

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).blg $(MAIN).log $(MAIN).out $(MAIN).pdf $(MAIN).synctex.gz

distclean: clean
	rm -rf figures
