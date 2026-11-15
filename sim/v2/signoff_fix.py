"""Re-run the window sweeps at SS (1.60 V) and FF (1.95 V) after fixing the input amplitude in tb.py
(inputs previously swung to 1.8 V at every corner). Updates data/v2/signoff_windows.csv in place."""
from multiprocessing import Pool
import pandas as pd
from signoff import task
from ngs import DATA
J = [("win", v, c, None) for c in (("ss", 100, 1.60), ("ff", -40, 1.95)) for v in ("schematic", "pex")]
if __name__ == "__main__":
    with Pool(4) as p:
        new = pd.DataFrame([r for k, r in p.map(task, J)])
    W = pd.read_csv(DATA / "signoff_windows.csv")
    W = pd.concat([W[~W.corner.isin(["ss", "ff"])], new]).sort_values(["corner", "view"])
    W.to_csv(DATA / "signoff_windows.csv", index=False)
    print(W.round(3).to_string())
