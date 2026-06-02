/* Analog macro — layout in layout/magic/, GDS/LEF in macros/
 * Black-box at RTL; OpenLane uses LEF for placement only.
 */
`default_nettype none

module fgmos_rtl_cell (
    input  wire VDD,
    input  wire VSS,
    output wire VOUT,
    input  wire A,
    input  wire B,
    input  wire C,
    input  wire VCTRL
);
    // LVS/spice reference: layout/xschem/fgmos_rtl.sp
endmodule
