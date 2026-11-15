#!/usr/bin/env bash
# Build the Zenodo archive (code + design files + results; no manuscript). Usage: bash make_bundle.sh 1.1
set -euo pipefail
cd "$(dirname "$0")"
VER=${1:-1.1}
B=dist/qfg-tlg-sky130
rm -rf "$B" && mkdir -p $B/sim/v2 $B/data $B/spice $B/env $B/layout/v2/{cells,magic,lvs,klayout,openroad/out}
rsync -a --exclude _runs --exclude __pycache__ --exclude make_paper_assets.py --exclude run_campaign.sh sim/v2/ $B/sim/v2/
rsync -a data/v2 $B/data/
rsync -a spice/v2 $B/spice/
cp layout/v2/{gen_layout.py,gen_layout_k.py,magparse.py,run_layout.sh,verify.sh,verify_k.sh} $B/layout/v2/
cp layout/v2/cells/gen_devs.tcl $B/layout/v2/cells/
cp layout/v2/magic/{qfg_tlg.mag,qfg_tlg.gds,drc.tcl,extract.tcl,qfg_tlg_lvs.spice,qfg_tlg_pex.spice,drc_report.txt} layout/v2/magic/sky130_fd_pr__*.mag $B/layout/v2/magic/
cp layout/v2/lvs/{qfg_tlg_schematic.spice,lvs_report.txt} $B/layout/v2/lvs/
cp layout/v2/klayout/{render.py,sky130A_full.lydrc,qfg_tlg_klayout_drc_full.xml,qfg_tlg_layout.png} $B/layout/v2/klayout/
cp layout/v2/openroad/{baselines.v,synth.ys.tmpl,pnr.tcl,tracks.tcl,run.sh} $B/layout/v2/openroad/
cp layout/v2/openroad/out/*.{metrics.txt,timing.rpt,power.rpt,synth_stat.txt,syn.v} $B/layout/v2/openroad/out/
for K in 5 9; do
  D=$B/layout/v2k/K$K; mkdir -p $D/{magic,lvs,klayout}
  cp layout/v2k/K$K/magic/qfg_tlg_k$K.{mag,gds} layout/v2k/K$K/magic/qfg_tlg_k${K}_{lvs,pex}.spice layout/v2k/K$K/magic/drc_report.txt layout/v2k/K$K/magic/sky130_fd_pr__*.mag $D/magic/
  cp layout/v2k/K$K/lvs/{qfg_tlg_k${K}_schematic.spice,lvs_report.txt} $D/lvs/
  cp layout/v2k/K$K/klayout/{qfg_tlg_k${K}_drc.xml,qfg_tlg_k${K}_layout.png} $D/klayout/
done
# keep the portable environment files and licences from the v1.0 bundle templates
cp -r dist_templates/* $B/ 2>/dev/null || true
# scrub local paths and make tool paths portable
grep -rIl "/Users/" $B | while read -r f; do sed -i '' "s#$(pwd)/#./#g; s#/Users/[^/ \"']*/#~/#g" "$f"; done
grep -rIl "/nix/store" $B | while read -r f; do sed -i '' "s#/nix/store/[^\" ]*/bin/ngspice#ngspice#g" "$f"; done
python3 - "$B" <<'EOF'
import sys, pathlib
b = pathlib.Path(sys.argv[1])
for f, src in [("layout/v2/verify.sh", "../../.eda/env.sh"), ("layout/v2/run_layout.sh", "../../.eda/env.sh"),
               ("layout/v2/verify_k.sh", "../../.eda/env.sh"), ("layout/v2/openroad/run.sh", "../../../.eda/env.sh")]:
    p = b / f; s = p.read_text()
    s = s.replace(f"source {src}\n", f"[ -f {src} ] && source {src}   # optional, see env/env.sh.example\n")
    s = s.replace(f"[ -f {src} ] && [ -f {src} ] && source {src}", f"[ -f {src} ] && source {src}")
    s = s.replace("../../../.eda/venv/bin/python", "${PYTHON:-python3}").replace("../../.eda/venv/bin/python", "${PYTHON:-python3}")
    s = s.replace("PY=${PYTHON:-$(cd ../.. && pwd)/.eda/venv/bin/python}", "PY=${PYTHON:-python3}")
    p.write_text(s)
EOF
find $B -name ".DS_Store" -delete
(cd dist && rm -f qfg-tlg-sky130-v$VER.zip && zip -qr qfg-tlg-sky130-v$VER.zip qfg-tlg-sky130)
grep -rIl -E "/Users/|/nix/store" $B || echo "no local paths"
ls -la dist/qfg-tlg-sky130-v$VER.zip
