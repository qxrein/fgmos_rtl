(.venv) sneha@DESKTOP-EEB32NG:~/fgmos_rtl$ pip install -r requirements.txt
Requirement already satisfied: numpy>=1.24 in ./.venv/lib/python3.12/site-packages (from -r requirements.txt (line 1)) (2.4.6)
Collecting scipy>=1.10 (from -r requirements.txt (line 2))
  Using cached scipy-1.17.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl.metadata (62 kB)
Requirement already satisfied: matplotlib>=3.7 in ./.venv/lib/python3.12/site-packages (from -r requirements.txt (line 3)) (3.10.9)
Collecting pandas>=2.0 (from -r requirements.txt (line 4))
  Using cached pandas-3.0.3-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (79 kB)
Collecting PySpice>=1.5 (from -r requirements.txt (line 5))
  Using cached PySpice-1.5-py2.py3-none-any.whl.metadata (15 kB)
Collecting schemdraw>=0.18 (from -r requirements.txt (line 6))
  Using cached schemdraw-0.23-py3-none-any.whl.metadata (2.2 kB)
Collecting gdstk>=0.9 (from -r requirements.txt (line 7))
  Using cached gdstk-1.0.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl.metadata (8.8 kB)
Requirement already satisfied: contourpy>=1.0.1 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (1.3.3)
Requirement already satisfied: cycler>=0.10 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (0.12.1)
Requirement already satisfied: fonttools>=4.22.0 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (4.63.0)
Requirement already satisfied: kiwisolver>=1.3.1 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (1.5.0)
Requirement already satisfied: packaging>=20.0 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (26.2)
Requirement already satisfied: pillow>=8 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (12.2.0)
Requirement already satisfied: pyparsing>=3 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (3.3.2)
Requirement already satisfied: python-dateutil>=2.7 in ./.venv/lib/python3.12/site-packages (from matplotlib>=3.7->-r requirements.txt (line 3)) (2.9.0.post0)
Requirement already satisfied: PyYAML>=5.3 in ./.venv/lib/python3.12/site-packages (from PySpice>=1.5->-r requirements.txt (line 5)) (6.0.3)
Collecting cffi>=1.14 (from PySpice>=1.5->-r requirements.txt (line 5))
  Using cached cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl.metadata (2.6 kB)
Collecting ply>=3.11 (from PySpice>=1.5->-r requirements.txt (line 5))
  Using cached ply-3.11-py2.py3-none-any.whl.metadata (844 bytes)
Collecting requests>=2.23 (from PySpice>=1.5->-r requirements.txt (line 5))
  Using cached requests-2.34.2-py3-none-any.whl.metadata (4.8 kB)
Collecting pycparser (from cffi>=1.14->PySpice>=1.5->-r requirements.txt (line 5))
  Using cached pycparser-3.0-py3-none-any.whl.metadata (8.2 kB)
Requirement already satisfied: six>=1.5 in ./.venv/lib/python3.12/site-packages (from python-dateutil>=2.7->matplotlib>=3.7->-r requirements.txt (line 3)) (1.17.0)
Collecting charset_normalizer<4,>=2 (from requests>=2.23->PySpice>=1.5->-r requirements.txt (line 5))
  Using cached charset_normalizer-3.4.7-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl.metadata (40 kB)
Requirement already satisfied: idna<4,>=2.5 in ./.venv/lib/python3.12/site-packages (from requests>=2.23->PySpice>=1.5->-r requirements.txt (line 5)) (3.18)
Collecting urllib3<3,>=1.26 (from requests>=2.23->PySpice>=1.5->-r requirements.txt (line 5))
  Using cached urllib3-2.7.0-py3-none-any.whl.metadata (6.9 kB)
Requirement already satisfied: certifi>=2023.5.7 in ./.venv/lib/python3.12/site-packages (from requests>=2.23->PySpice>=1.5->-r requirements.txt (line 5)) (2026.5.20)
Using cached scipy-1.17.1-cp312-cp312-manylinux_2_27_x86_64.manylinux_2_28_x86_64.whl (35.2 MB)
Using cached pandas-3.0.3-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (10.9 MB)
Using cached PySpice-1.5-py2.py3-none-any.whl (158 kB)
Using cached schemdraw-0.23-py3-none-any.whl (152 kB)
Using cached gdstk-1.0.0-cp312-cp312-manylinux_2_24_x86_64.manylinux_2_28_x86_64.whl (541 kB)
Using cached cffi-2.0.0-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl (219 kB)
Using cached ply-3.11-py2.py3-none-any.whl (49 kB)
Using cached requests-2.34.2-py3-none-any.whl (73 kB)
Using cached charset_normalizer-3.4.7-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl (216 kB)
Using cached urllib3-2.7.0-py3-none-any.whl (131 kB)
Using cached pycparser-3.0-py3-none-any.whl (48 kB)
Installing collected packages: ply, urllib3, scipy, schemdraw, pycparser, gdstk, charset_normalizer, requests, pandas, cffi, PySpice
Successfully installed PySpice-1.5 cffi-2.0.0 charset_normalizer-3.4.7 gdstk-1.0.0 pandas-3.0.3 ply-3.11 pycparser-3.0 requests-2.34.2 schemdraw-0.23 scipy-1.17.1 urllib3-2.7.0
(.venv) sneha@DESKTOP-EEB32NG:~/fgmos_rtl$ export PDK_ROOT=/home/sneha/share/pdk
export PDK=sky130A
source layout/setup_pdk.sh

make -C layout magic magic-extract klayout-drc
python sim/postlayout_signoff.py      # ngspice only
python sim/signoff_analysis.py      # full sign-off tables/figures
# or: python sim/main.py            # runs layout + everything if PDK_ROOT is set
PDK_ROOT=/home/sneha/share/pdk  PDK=sky130A  magic=/home/sneha/local/bin/magic 8.3.652
make: Entering directory '/home/sneha/fgmos_rtl/layout'
cd magic && ./run_magic_layout.sh
==> Magic layout (batch)
==> GDS: export/fgmos_rtl_cell.gds
==> DRC (if layout present)
Done. Copy export/*.gds to ../openlane/fgmos_rtl_wrapper/macros/
cd magic && ./run_magic_extract.sh
==> Magic extraction
==> Netgen LVS
NETGEN-6.2.2401
Developed by Joachim Schoeberl at
2010-xxxx Vienna University of Technology
2006-2010 RWTH Aachen University
1996-2006 Johannes Kepler University Linz
Including OpenCascade geometry kernel
Including MPI version 3.1
Error in Tcl-Script:
result = couldn't load file "libnggui.so": libnggui.so: cannot open shared object file: No such file or directory

Make sure to set environment variable NETGENDIR to directory containing ng.tcl
==> LVS log: export/fgmos_rtl_cell_lvs.log
Done.
bash klayout/run_drc.sh
==> KLayout DRC: /home/sneha/fgmos_rtl/layout/magic/export/fgmos_rtl_cell.gds
"ongrid" in: sky130A.lydrc:897
    Edge pairs: 0 (flat)  0 (hierarchical)
    Elapsed: 0.000s  Memory: 1125.00M
"output" in: sky130A.lydrc:897
    Edge pairs: 0 (flat)  0 (hierarchical)
    Elapsed: 0.000s  Memory: 1125.00M
"with_angle" in: sky130A.lydrc:898
    Edge pairs: 0 (flat)  0 (hierarchical)
    Elapsed: 0.000s  Memory: 1125.00M
"output" in: sky130A.lydrc:898
    Edge pairs: 0 (flat)  0 (hierarchical)
    Elapsed: 0.000s  Memory: 1125.00M
"ongrid" in: sky130A.lydrc:899
    Edge pairs: 0 (flat)  0 (hierarchical)
    Elapsed: 0.000s  Memory: 1125.00M
"output" in: sky130A.lydrc:899
    Edge pairs: 0 (flat)  0 (hierarchical)
    Elapsed: 0.000s  Memory: 1125.00M
Writing report database: /home/sneha/fgmos_rtl/data/klayout_drc_fgmos.txt ..
Total elapsed: 0.480s  Memory: 1125.00M
==> Report: /home/sneha/fgmos_rtl/data/klayout_drc_fgmos.txt
make: Leaving directory '/home/sneha/fgmos_rtl/layout'
  Post-layout: extracted FG-related C sum ≈ 0.5 fF
  Post-layout: R_eff 0.61–572.52 kΩ (938.1×), τ≈168 ps @ median
  Post-layout: extracted FG-related C sum ≈ 0.5 fF
  Post-layout: R_eff 0.61–572.52 kΩ (938.1×), τ≈168 ps @ median
  Sign-off: fig9/fig10 updated (B&W); tables in tables/
  Mismatch logic OK: 100.0%
  Post-layout ngspice: R_eff ratio 938.1×, τ≈168.0 ps
