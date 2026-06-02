/* LibreLane-synthesizable harness for fgmos_rtl MPW wrapper.
 * Analog fgmos_rtl_cell macro is black-boxed when GDS/LEF are in macros/;
 * this RTL provides clock + GPIO for placement/routing smoke tests.
 */
`default_nettype none

module fgmos_rtl_wrapper (
    input  wire       clk,
    input  wire       rst_n,
    input  wire [2:0] pad_a,
    input  wire [2:0] pad_b,
    input  wire [7:0] pad_vctrl,
    output wire       pad_vout
);

    wire [2:0] mode_sel;
    reg  [7:0] ctrl_reg;
    reg  [2:0] out_reg;

    assign mode_sel = pad_a ^ pad_b;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            ctrl_reg <= 8'd0;
            out_reg  <= 3'd0;
        end else begin
            ctrl_reg <= pad_vctrl;
            out_reg  <= mode_sel + ctrl_reg[2:0];
        end
    end

    assign pad_vout = |out_reg;

    // Tie-off for future Magic macro (uncomment when macros/ populated)
    // fgmos_rtl_cell u_fgmos (...);

endmodule
