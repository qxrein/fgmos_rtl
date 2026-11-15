load qfg_tlg_k5
select top cell
port makeall
# --- LVS netlist (devices only) ---
extract do local
extract all
ext2spice lvs
ext2spice -o qfg_tlg_k5_lvs.spice
# --- parasitic (C) netlist for post-layout simulation ---
extract all
ext2spice lvs
ext2spice cthresh 0
ext2spice rthresh 0
ext2spice -o qfg_tlg_k5_pex.spice
# --- GDS for KLayout DRC / figures ---
gds write qfg_tlg_k5.gds
# bounding box (um)
set bb [box values]
select top cell
puts "BBOX [lmap v [box values] {expr {$v*0.005}}]"
save qfg_tlg_k5
quit -noprompt
