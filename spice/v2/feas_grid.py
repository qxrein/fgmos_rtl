import subprocess, numpy as np, itertools, os
NG="/nix/store/8xash38paka9by07h83bb602rsjkd4kg-ngspice-45/bin/ngspice"
LIB="/Users/rein/projects/fgmos_rtl/.eda/pdk/sky130A/libs.tech/ngspice/sky130.lib.spice"
def run(Wp,Wn,Cin,Cc):
    deck=f"""* grid
.lib "{LIB}" tt
.option scale=1.0u
.param n=0
Vcc vcc 0 1.8
Vctrl vctrl 0 0.9
Bfg fg 0 V = ({Cin}f*1.8*n + {Cc}f*v(vctrl))/({3*Cin}f+{Cc}f+3f)
XMp out fg vcc vcc sky130_fd_pr__pfet_01v8 W={Wp} L=0.15
Va a 0 {{1.8*(n>=1)}}
Vb b 0 {{1.8*(n>=2)}}
Vc c 0 {{1.8*(n>=3)}}
XMa out a 0 0 sky130_fd_pr__nfet_01v8 W={Wn} L=0.15
XMb out b 0 0 sky130_fd_pr__nfet_01v8 W={Wn} L=0.15
XMc out c 0 0 sky130_fd_pr__nfet_01v8 W={Wn} L=0.15
.control
foreach nn 0 1 2 3
  alterparam n = $nn
  reset
  dc Vctrl 0 1.8 0.02
  set fname = g_n{{$nn}}.txt
  wrdata $fname v(out)
end
.endc
.end
"""
    open("g.sp","w").write(deck)
    subprocess.run([NG,"-b","g.sp"],capture_output=True)
    d=[np.loadtxt(f"g_n{k}.txt") for k in range(4)]
    vc=d[0][:,0]; V=np.array([x[:,1] for x in d]).T
    pats=[''.join('1' if x>1.35 else ('0' if x<0.45 else '?') for x in row) for row in V]
    res={}
    for p,name in [("1000","NOR"),("1100","MIN"),("1110","NAND")]:
        idx=[i for i,q in enumerate(pats) if q==p]
        res[name]=(vc[idx[0]],vc[idx[-1]]) if idx else None
    return res
for Wp,Wn,Cin,Cc in itertools.product([2,4,6],[0.42,0.65],[5,8],[20,30]):
    r=run(Wp,Wn,Cin,Cc)
    ok=all(r.values())
    print(Wp,Wn,Cin,Cc, {k:(None if v is None else (round(v[0],2),round(v[1],2))) for k,v in r.items()}, "ALL3" if ok else "")
