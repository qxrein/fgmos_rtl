load probe -silent
proc gen {name dev x y args} {
  box values $x $y $x $y
  magic::gencell sky130::$dev $name {*}$args
}
gen XMP sky130_fd_pr__pfet_01v8 0 0 w 4.0 l 0.15 nf 4 conn_gates 1 viagt 100 full_metal 1
gen XMN sky130_fd_pr__nfet_01v8 3000 0 w 0.42 l 0.15 nf 1 viagb 100
gen XC  sky130_fd_pr__cap_mim_m3_1 6000 0 w 2.0 l 2.0
gen XCB sky130_fd_pr__cap_mim_m3_1 9000 0 w 4.85 l 4.85
writeall force
puts "DONE"
quit -noprompt
