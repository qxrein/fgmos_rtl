load qfg_tlg
select top cell
expand
drc euclidean on
drc style drc(full)
drc check
drc catchup
set n [drc list count total]
puts "DRCCOUNT $n"
set f [open drc_report.txt w]
foreach {why boxes} [drc listall why] {
  puts $f "== $why ([llength $boxes])"
  foreach b [lrange $boxes 0 5] { puts $f "   [lmap v $b {expr {$v*0.005}}]" }
}
close $f
quit -noprompt
