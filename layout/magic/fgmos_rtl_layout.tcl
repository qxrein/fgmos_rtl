# FGMOS-RTL analog macro — automated Sky130A layout (batch Magic)
# Places FGMOS pull-up, three input NFETs, five MIM coupling caps, ties, FG/VOUT buses.

if {![info exists env(PDK_ROOT)]} {
    puts stderr "ERROR: export PDK_ROOT and PDK=sky130A"
    exit 1
}
if {![info exists env(PDK)]} {
    set env(PDK) sky130A
}

scalegrid 1 2
tech unlock *

catch {flush fgmos_rtl_cell}
load fgmos_rtl_cell

proc _place_nfet {x y {w 2.0} {l 0.15}} {
    set p [dict merge [sky130::sky130_fd_pr__nfet_01v8_defaults] [list w $w l $l doports 1]]
    pushbox
    box values $x $y $x $y
    sky130::sky130_fd_pr__nfet_01v8_draw $p
    popbox
}

proc _place_mim {x y {w 2.0} {l 2.0}} {
    set p [dict merge [sky130::sky130_fd_pr__cap_mim_m3_1_defaults] [list w $w l $l doports 1]]
    pushbox
    box values $x $y $x $y
    sky130::sky130_fd_pr__cap_mim_m3_1_draw $p
    popbox
}

proc _paint_rect {layer x0 y0 x1 y1} {
    pushbox
    box values $x0 $y0 $x1 $y1
    paint $layer
    popbox
}

# --- devices (microns), spaced to avoid merge ---
# Main FGMOS pull-up
_place_nfet 24 10
# Input NFETs (A, B, C)
_place_nfet 6  26
_place_nfet 24 26
_place_nfet 42 26
# MIM coupling capacitors (bottom on met3 FG bus)
_place_mim 4  44
_place_mim 14 44
_place_mim 24 44
_place_mim 34 44
_place_mim 44 44

# VSS substrate tie (>= 0.17 um width)
pushbox
box values 4 0 48 1.2
sky130::subconn_draw
popbox

# VOUT: met2 drain bus
_paint_rect met2 4 7 48 9
# VSS: met1 source/substrate strap
_paint_rect met1 4 0.5 48 2
# FG floating-gate bus (met3) — main device gate + cap tops only
_paint_rect met3 2 48 50 50.5
# Per-input gate straps (do NOT tie to FG)
_paint_rect met1 5  26 7  30
_paint_rect met1 23 26 25 30
_paint_rect met1 41 26 43 30
# Tie main FGMOS gate to FG bus (met1 stub)
_paint_rect met1 23 10 25 48
# VCTRL cap anchor
_paint_rect met3 42 44 46 50.5

# Top-level port labels (layer type, not font)
label VOUT metal2 26 8 center
label VSS  metal1 26 1 center
label FG   metal3 26 49 center
label A    metal1 6  28 center
label B    metal1 24 28 center
label C    metal1 42 28 center
label VCTRL metal3 44 47 center
label VDD  metal2 46 8 center

file mkdir export
save fgmos_rtl_cell
catch {gds write export/fgmos_rtl_cell.gds}

drc check
drc catchup
puts "INFO: DRC violations: [drc listall count]"
puts "INFO: Wrote export/fgmos_rtl_cell.gds"
