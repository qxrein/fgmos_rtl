/* Digital harness: pad-facing GPIO + clock for MPW test
 * Drives fgmos_rtl_cell macro exported from Magic.
 */
`default_nettype none

module fgmos_rtl_wrapper (
    input  wire clk,
    input  wire rst_n,
    input  wire [2:0] pad_a,
    input  wire [2:0] pad_b,
    input  wire [7:0] pad_vctrl,
    output wire       pad_vout,
    inout  wire vccd1,
    inout  wire vssd1
);

    wire [2:0] a, b;
    wire [7:0] vctrl_bus;
    wire vout_analog;

    // Simplified pad mapping (replace with sky130 IO cells in hardened flow)
    assign a    = pad_a;
    assign b    = pad_b;
    assign vctrl_bus = pad_vctrl;

    fgmos_rtl_cell u_fgmos (
        .VDD   (vccd1),
        .VSS   (vssd1),
        .VOUT  (vout_analog),
        .A     (a[0]),
        .B     (a[1]),
        .C     (a[2]),
        .VCTRL (vctrl_bus[0])
    );

    // Comparator / buffer placeholder — tapeout may use sky130_io
    assign pad_vout = vout_analog;

endmodule
