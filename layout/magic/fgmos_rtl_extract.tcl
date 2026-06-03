# FGMOS-RTL macro extraction for Magic batch mode
# Expects: PDK_ROOT and PDK set in environment

if {![info exists env(PDK_ROOT)]} {
    puts stderr "ERROR: export PDK_ROOT and PDK=sky130A"
    exit 1
}

if {![info exists env(PDK)]} {
    set env(PDK) "sky130A"
}

set pdk $env(PDK)

if {[file exists "fgmos_rtl_cell.mag"]} {
    load fgmos_rtl_cell
} else {
    puts stderr "ERROR: fgmos_rtl_cell.mag not found. Run layout first."
    exit 1
}

file mkdir export

drc check
drc catchup
drc count total

extract all
ext2spice lvs
ext2spice cthresh 0.01 rthresh 0.01
ext2spice subcircuit on
ext2spice hierarchy on
ext2spice renumber off
ext2spice format ngspice
port makeall
ext2spice -o export/fgmos_rtl_cell_extracted.spice

save fgmos_rtl_cell
puts "INFO: wrote export/fgmos_rtl_cell_extracted.spice"
