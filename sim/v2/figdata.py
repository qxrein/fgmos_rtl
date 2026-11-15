"""Raw curves for figures: TT VB sweeps (schematic and PEX, all 8 minterms) and TT waveforms."""
from multiprocessing import Pool
import shutil
from pathlib import Path
import pandas as pd
from ngs import DATA, pex_cell_text
from tb import vb_sweep
from tbseq import seq_run

def sweep(view):
    df = vb_sweep(corner="tt", vb_lo=-0.05, vb_hi=1.25, vb_step=0.005, tag=f"fig_{view}",
                  cell_text=pex_cell_text() if view == "pex" else None)
    df["view"] = view
    return df

def waves(view):
    df = seq_run(vbs=(0.307, 0.571, 0.849), tag=f"figw_{view}", save_wave=True, t_p=0.3,
                 cell_text=pex_cell_text() if view == "pex" else None)
    d = Path(df.attrs["dir"])
    for f in d.glob("wave_*.txt"):
        shutil.copy(f, DATA / f"wave_{view}_{f.stem.split('_')[1]}.txt")
    return view

if __name__ == "__main__":
    with Pool(4) as p:
        sw = p.map_async(sweep, ["schematic", "pex"])
        wv = p.map_async(waves, ["schematic", "pex"])
        pd.concat(sw.get()).to_csv(DATA / "fig_vbsweep_tt.csv", index=False)
        print(wv.get())
