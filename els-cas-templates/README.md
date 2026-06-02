# FGMOS-RTL paper (Elsevier CAS)

Self-contained manuscript directory for the Microelectronics / VLSI journal submission.

## Contents

| File | Description |
|------|-------------|
| `article.tex` | Main manuscript |
| `report.bib` | Bibliography |
| `figures/` | Paper figures (`fig1`--`fig7`, PDF + PNG) |
| `cas-sc.cls`, `cas-common.sty`, `cas-model2-names.bst` | Elsevier CAS class files |

## Figure layout

The Elsevier template snippet `\def\floatpagepagefraction{1}` must **not** be used in the body of `article.tex`; it pushes every figure to the end. Figures are set to `0.62\linewidth` (and paired panels at `0.48\linewidth`) so matplotlib exports do not fill the entire page.

## Build

```bash
# Regenerate figures at repo root, then build PDF
cd ..
python sim/main.py
make -C els-cas-templates
```

`make figures` copies `../figures/fig*.pdf` into `els-cas-templates/figures/`.

## Overleaf

Zip or upload this entire `els-cas-templates/` folder. Set the main document to `article.tex`. No path prefixes are required for figures.

## Author information

Edit `\author`, `\affiliation`, and `\ead` in `article.tex` before submission.
