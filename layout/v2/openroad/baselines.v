// Standard-cell baselines for the reconfigurable threshold-logic comparison.
// Configuration is held in a scan-loaded flip-flop chain (cfg_clk / cfg_in),
// the usual way a soft/eFPGA cell stores its function.

// (a) Same function set as the QFG cell: OR3 / MAJ3 / AND3 selected by 2 config bits.
module recfg3_mux (input a, b, c, input cfg_clk, cfg_in, output y);
  reg [1:0] s;
  always @(posedge cfg_clk) s <= {s[0], cfg_in};
  wire f_or  = a | b | c;
  wire f_maj = (a & b) | (b & c) | (a & c);
  wire f_and = a & b & c;
  assign y = (s == 2'd0) ? f_or : (s == 2'd1) ? f_maj : f_and;
endmodule

// (b) k-input LUT: 2^k config bits + 2^k:1 multiplexer (any k-input function).
module lut_k #(parameter K = 3) (input [K-1:0] x, input cfg_clk, cfg_in, output y);
  reg [(1<<K)-1:0] t;
  always @(posedge cfg_clk) t <= {t[(1<<K)-2:0], cfg_in};
  assign y = t[x];
endmodule

// (c) Reconfigurable symmetric threshold gate: y = (popcount(x) >= T), T programmable.
//     Same function family as a k-input QFG threshold cell.
module thr_k #(parameter K = 3, parameter TB = 2) (input [K-1:0] x, input cfg_clk, cfg_in, output y);
  reg [TB-1:0] T;
  always @(posedge cfg_clk) T <= {T[TB-2:0], cfg_in};
  integer i;
  reg [TB:0] cnt;
  always @(*) begin
    cnt = 0;
    for (i = 0; i < K; i = i + 1) cnt = cnt + x[i];
  end
  assign y = (cnt >= T);
endmodule

module lut3 (input [2:0] x, input cfg_clk, cfg_in, output y); lut_k #(3) u(.x(x),.cfg_clk(cfg_clk),.cfg_in(cfg_in),.y(y)); endmodule
module lut5 (input [4:0] x, input cfg_clk, cfg_in, output y); lut_k #(5) u(.x(x),.cfg_clk(cfg_clk),.cfg_in(cfg_in),.y(y)); endmodule
module lut7 (input [6:0] x, input cfg_clk, cfg_in, output y); lut_k #(7) u(.x(x),.cfg_clk(cfg_clk),.cfg_in(cfg_in),.y(y)); endmodule
module thr3 (input [2:0] x, input cfg_clk, cfg_in, output y); thr_k #(3,2) u(.x(x),.cfg_clk(cfg_clk),.cfg_in(cfg_in),.y(y)); endmodule
module thr5 (input [4:0] x, input cfg_clk, cfg_in, output y); thr_k #(5,3) u(.x(x),.cfg_clk(cfg_clk),.cfg_in(cfg_in),.y(y)); endmodule
module thr7 (input [6:0] x, input cfg_clk, cfg_in, output y); thr_k #(7,3) u(.x(x),.cfg_clk(cfg_clk),.cfg_in(cfg_in),.y(y)); endmodule
module thr9 (input [8:0] x, input cfg_clk, cfg_in, output y); thr_k #(9,4) u(.x(x),.cfg_clk(cfg_clk),.cfg_in(cfg_in),.y(y)); endmodule
module fixed_maj3 (input a, b, c, output y); assign y = (a & b) | (b & c) | (a & c); endmodule
