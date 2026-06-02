# Overleaf Import Guide

## Recommended: full CAS manuscript
Upload the entire `els-cas-templates/` folder and set the main document to `article.tex`.
Figures are already in `els-cas-templates/figures/`.

## Alternative: figures only
## Step 1 — Upload
In Overleaf: click Upload → select entire figures/ and tables/ directories.

## Step 2 — Include figures in paper
```latex
\begin{figure}[h]
  \centering
  \includegraphics[width=\columnwidth]{figures/fig1_rtl_schematic}
  \caption{Proposed FGMOS-RTL cell. The base resistor of conventional RTL 
           is replaced by an FGMOS operating in ohmic region.}
  \label{fig:schematic}
\end{figure}

\includegraphics[width=\columnwidth]{figures/fig2_Reff_vs_Vfg}
\includegraphics[width=\columnwidth]{figures/fig3_logic_heatmap}
\includegraphics[width=\columnwidth]{figures/fig4_pbit_sigmoid}
\includegraphics[width=\columnwidth]{figures/fig5_transition_width}
\includegraphics[width=\columnwidth]{figures/fig6_autocorrelation}
\includegraphics[width=\columnwidth]{figures/fig7_summary_comparison}
```

## Step 3 — Include tables
```latex
\input{tables/table1_truth_table}
\input{tables/table2_prior_art}
\input{tables/table3_spice_params}
```

## Step 4 — Elsevier template (AEU / VLSI Journal)
Use: `\documentclass[preprint,12pt]{elsarticle}`
Download free from: https://www.elsevier.com/researcher/author/policies-and-guidelines/latex-instructions
