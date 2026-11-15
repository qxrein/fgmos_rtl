load qfg_tlg
select top cell
port makeall
# --- LVS netlist (devices only) ---
extract do local
extract all
ext2spice lvs
ext2spice -o qfg_tlg_lvs.spice
# --- parasitic (C) netlist for post-layout simulation ---
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice rthresh 0
ext2spice -o qfg_tlg_pex.spice
# --- GDS for KLayout DRC / figures ---
gds write qfg_tlg.gds
# bounding box (um)
set bb [box values]
select top cell
puts "BBOX [lmap v [box values] {expr {$v*0.005}}]"
save qfg_tlg
quit -noprompt
