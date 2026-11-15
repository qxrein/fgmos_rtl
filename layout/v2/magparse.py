"""Parse Magic .mag files (magscale 1 2 => 1 unit = 0.005 um) into layer rects and labels (um)."""
import re
U = 0.005
def parse(path):
    layers, labels, bbox, layer = {}, [], None, None
    for ln in open(path):
        ln = ln.strip()
        m = re.match(r"<< (\S+) >>", ln)
        if m:
            layer = m.group(1); continue
        if ln.startswith("rect ") and layer not in ("checkpaint",):
            x1, y1, x2, y2 = [int(v) * U for v in ln.split()[1:5]]
            layers.setdefault(layer, []).append((x1, y1, x2, y2))
        elif ln.startswith("rlabel"):
            p = ln.split()
            labels.append((p[1], int(p[2]) * U, int(p[3]) * U, p[-1]))
        elif ln.startswith("string FIXED_BBOX"):
            bbox = tuple(int(v) * U for v in ln.split()[2:6])
    return dict(layers=layers, labels=labels, bbox=bbox)

def term_rect(d, layer, x, y):
    """Smallest rect on `layer` containing point (x,y)."""
    best = None
    for r in d["layers"].get(layer, []):
        if r[0] <= x <= r[2] and r[1] <= y <= r[3]:
            if best is None or (r[2]-r[0])*(r[3]-r[1]) < (best[2]-best[0])*(best[3]-best[1]):
                best = r
    return best

if __name__ == "__main__":
    import sys
    for line in open("cells/devmap.txt"):
        inst, cell = line.split()
        d = parse(f"cells/{cell}.mag")
        print(f"== {inst} {cell} bbox={d['bbox']}")
        for lab in d["labels"]:
            print("   label", lab)
        for L in ("metal1","metal3","metal4","mimcap","nwell","pwell"):
            if L in d["layers"]:
                rs = d["layers"][L]
                xs = [r[0] for r in rs]+[r[2] for r in rs]; ys=[r[1] for r in rs]+[r[3] for r in rs]
                print(f"   {L}: n={len(rs)} extent x[{min(xs):.3f},{max(xs):.3f}] y[{min(ys):.3f},{max(ys):.3f}]")
