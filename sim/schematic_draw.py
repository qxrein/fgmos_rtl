"""
Draw RTL cell circuit schematic using schemdraw (free, pip install schemdraw).
Generates: figures/fig1_rtl_schematic.pdf + .png
"""
import os

import matplotlib
matplotlib.use('Agg')
import schemdraw
import schemdraw.elements as elm


def run():
    os.makedirs('figures', exist_ok=True)
    cx = 5.0  # center column — labels placed left/right, not on wires

    with schemdraw.Drawing(show=False) as d:
        d.config(fontsize=8, unit=1.0)

        vcc = d.add(elm.Dot().at((cx, 7.5)))
        d.add(elm.Label().at((cx, 8.15)).label('$V_{CC}=1.8\\,\\mathrm{V}$', loc='center'))

        d.add(elm.Line().at(vcc.end).down().length(0.7))
        R = d.add(elm.ResistorIEEE().down().length(1.1))
        d.add(elm.Line().down().length(0.45))
        vout = d.add(elm.Dot())
        d.add(elm.Line().down().length(0.45))
        Q = d.add(elm.BjtNpn(circle=True))
        d.add(elm.Line().at(Q.emitter).down().length(0.55))
        d.add(elm.Ground())

        # Labels offset from symbols — avoids overlap with wires
        d.add(elm.Label().at((cx + 1.35, (R.start.y + R.end.y) / 2))
              .label('FGMOS $R_{eff}(V_{fg})$', loc='center'))
        d.add(elm.Label().at((cx + 1.05, vout.center.y))
              .label('$V_{out}$', loc='left'))
        d.add(elm.Label().at((cx + 1.45, Q.center.y))
              .label('$M_{in}$ (Sky130 nfet)', loc='left'))

        # Control bus — tap left of resistor top; text left of the horizontal wire
        ctrl_x = cx - 2.4
        d.add(elm.Line().at(R.start).left().length(cx - ctrl_x))
        d.add(elm.Label().at((ctrl_x - 0.15, R.start.y + 0.22))
              .label('$V_{ctrl}$', loc='right'))
        d.add(elm.Label().at((ctrl_x - 0.15, R.start.y - 0.22))
              .label('(weight bus)', loc='right', fontsize=7))

        # Input — gate line left; label below the horizontal segment
        vin_y = Q.base.y - 0.55
        d.add(elm.Line().at(Q.base).left().length(1.6))
        d.add(elm.Label().at((cx - 1.6 - 0.1, vin_y))
              .label('$V_{in}$ (A,B,C)', loc='right'))

    d.save('figures/fig1_rtl_schematic.pdf')
    d.save('figures/fig1_rtl_schematic.png', dpi=300)
    print("  fig1_rtl_schematic saved ✅")
