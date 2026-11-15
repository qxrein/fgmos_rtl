# Step 1 of the v2 layout flow: generate each distinct device as a standalone Magic cell.
# Gates are contacted at the BOTTOM (facing the capacitor block); tap rings are strapped at the TOP.
load devs -silent
proc gen {name dev x args} {
  box values ${x}um 0um ${x}um 0um
  magic::gencell sky130::$dev $name {*}$args
}
gen MP  sky130_fd_pr__pfet_01v8 0   w 4.0  l 0.15 nf 4 conn_gates 1 topc 0 botc 1 viagb 0 viagt 70
gen MIP sky130_fd_pr__pfet_01v8 10  w 1.0  l 0.15 nf 1 topc 0 botc 1 viagb 0 viagt 70
gen MN  sky130_fd_pr__nfet_01v8 20  w 0.42 l 0.15 nf 1 topc 0 botc 1 viagb 0 viagt 70
gen MR  sky130_fd_pr__nfet_01v8 30  w 0.42 l 0.5  nf 1 topc 0 botc 1 viagb 0 viagt 70
writeall force
set f [open devmap.txt w]
foreach inst {MP MIP MN MR} { puts $f "$inst [instance list celldef $inst]" }
close $f
puts "DONE"
quit -noprompt
