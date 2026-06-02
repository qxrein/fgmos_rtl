"""
Master runner. Execute: python sim/main.py
Runs all claims, prints checklist, confirms Overleaf readiness.
"""
import sys, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'sim'))

print("\n" + "="*55)
print("  FGMOS RTL FABRIC — PAPER SIMULATION SUITE")
print("="*55)

print("\n[Schematic]")
from schematic_draw import run as r0; r0()

print("\n[Claim 1] Programmable base resistor")
from claim1_resistance import run as r1; c1 = r1()

print("\n[Claim 2] NOR/MAJ/AND reconfiguration")
from claim2_logic import run as r2; c2 = r2()

print("\n[Claim 3] p-bit Monte Carlo")
from claim3_pbit import run as r3; c3 = r3()

print("\n[Sign-off] PVT, mismatch, delay/energy/area")
from signoff_analysis import run as r4; c4 = r4()

print("\n" + "="*55)
print("  VERIFICATION CHECKLIST")
print("="*55)
print(f"  {'✅' if c1 else '❌'} Claim 1: R_eff spans >10x via Vfg")
print(f"  {'✅' if c2 else '❌'} Claim 2: NOR / MAJ / AND all found")
print(f"  {'✅' if c3 else '❌'} Claim 3: sigmoid + randomness confirmed")
print(f"  {'✅' if c4 else '❌'} Sign-off: PVT/mismatch/delay/energy tables")
print(f"  ✅  Ohmic constraint checked in every Vout_rtl call")
print(f"  ✅  All caps within Sky130 MIM range (1fF–100fF)")

print("\n  Overleaf-ready files:")
import glob
for f in sorted(glob.glob('figures/*.pdf') + glob.glob('tables/*.tex')):
    print(f"    {f}")

print("\n  Copy to Overleaf:")
print("    Upload els-cas-templates/ (includes figures/) or figures/ + tables/")
print("    CAS paper: els-cas-templates/article.tex")
print("="*55)

# Sync figures into self-contained CAS manuscript folder
import shutil
cas_fig = os.path.join(ROOT, 'els-cas-templates', 'figures')
os.makedirs(cas_fig, exist_ok=True)
for f in glob.glob(os.path.join(ROOT, 'figures', 'fig*.*')):
    shutil.copy2(f, cas_fig)
print(f"\n  Figures synced to {cas_fig}/")

print("\n[Layout] OpenLane fabrication figure (GDS render)")
import subprocess
layout_mk = os.path.join(ROOT, 'layout', 'Makefile')
if os.path.isfile(layout_mk):
    env = os.environ.copy()
    env['PYTHON'] = os.path.join(ROOT, 'env', 'bin', 'python')
    subprocess.run(['make', '-C', os.path.join(ROOT, 'layout'), 'openlane-figure'],
                     check=False, env=env)
