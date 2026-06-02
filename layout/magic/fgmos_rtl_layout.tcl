# FGMOS-RTL analog macro — Sky130A Magic layout (starter)
# Completes placement in GUI if batch PDK cells are unavailable.
# Usage: ./run_magic_layout.sh

if {![info exists env(PDK_ROOT)]} {
    puts stderr "ERROR: export PDK_ROOT and PDK=sky130A"
    exit 1
}

if {![info exists env(PDK)]} {
    set env(PDK) "sky130A"
}

scalegrid 1 2

# Open/create the macro cell
load fgmos_rtl_cell

# Guide bounding box (~14 x 10 um in internal units)
box 0 0 14000 10000

puts "INFO: Created/loaded fgmos_rtl_cell guide canvas."
puts "INFO: Place sky130_fd_pr__nfet_01v8 and MIM caps manually in Magic GUI."
puts "INFO: Then rerun extraction with ./run_magic_extract.sh."

file mkdir export
save fgmos_rtl_cell
catch {gds write export/fgmos_rtl_cell.gds}
