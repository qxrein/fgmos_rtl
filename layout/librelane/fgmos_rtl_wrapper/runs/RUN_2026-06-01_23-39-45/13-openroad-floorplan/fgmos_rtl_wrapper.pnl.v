module fgmos_rtl_wrapper (clk,
    pad_vout,
    rst_n,
    vccd1,
    vssd1,
    pad_a,
    pad_b,
    pad_vctrl);
 input clk;
 output pad_vout;
 input rst_n;
 output vccd1;
 output vssd1;
 input [2:0] pad_a;
 input [2:0] pad_b;
 input [7:0] pad_vctrl;

 wire _00_;
 wire _01_;
 wire _02_;
 wire _03_;
 wire _04_;
 wire _05_;
 wire _06_;
 wire _07_;
 wire _08_;
 wire _09_;
 wire _10_;
 wire _11_;
 wire _12_;
 wire _13_;
 wire _14_;
 wire _15_;
 wire \ctrl_reg[0] ;
 wire \ctrl_reg[1] ;
 wire \ctrl_reg[2] ;
 wire \out_reg[0] ;
 wire \out_reg[1] ;
 wire \out_reg[2] ;
 wire VPWR;
 wire VGND;

 sky130_fd_sc_hd__or2_2 _16_ (.A(pad_b[0]),
    .B(pad_a[0]),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .X(_03_));
 sky130_fd_sc_hd__nand2_2 _17_ (.A(pad_b[0]),
    .B(pad_a[0]),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_04_));
 sky130_fd_sc_hd__and3_2 _18_ (.A(\ctrl_reg[0] ),
    .B(_03_),
    .C(_04_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .X(_05_));
 sky130_fd_sc_hd__or2_2 _19_ (.A(pad_b[1]),
    .B(pad_a[1]),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .X(_06_));
 sky130_fd_sc_hd__nand2_2 _20_ (.A(pad_b[1]),
    .B(pad_a[1]),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_07_));
 sky130_fd_sc_hd__a21oi_2 _21_ (.A1(_06_),
    .A2(_07_),
    .B1(\ctrl_reg[1] ),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_08_));
 sky130_fd_sc_hd__a21o_2 _22_ (.A1(_06_),
    .A2(_07_),
    .B1(\ctrl_reg[1] ),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .X(_09_));
 sky130_fd_sc_hd__and3_2 _23_ (.A(\ctrl_reg[1] ),
    .B(_06_),
    .C(_07_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .X(_10_));
 sky130_fd_sc_hd__or2_2 _24_ (.A(_08_),
    .B(_10_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .X(_11_));
 sky130_fd_sc_hd__xnor2_2 _25_ (.A(_05_),
    .B(_11_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_01_));
 sky130_fd_sc_hd__a21oi_2 _26_ (.A1(_05_),
    .A2(_09_),
    .B1(_10_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_12_));
 sky130_fd_sc_hd__xnor2_2 _27_ (.A(pad_a[2]),
    .B(\ctrl_reg[2] ),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_13_));
 sky130_fd_sc_hd__xnor2_2 _28_ (.A(pad_b[2]),
    .B(_13_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_14_));
 sky130_fd_sc_hd__xnor2_2 _29_ (.A(_12_),
    .B(_14_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_02_));
 sky130_fd_sc_hd__a21oi_2 _30_ (.A1(_03_),
    .A2(_04_),
    .B1(\ctrl_reg[0] ),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_15_));
 sky130_fd_sc_hd__nor2_2 _31_ (.A(_05_),
    .B(_15_),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Y(_00_));
 sky130_fd_sc_hd__or3_2 _32_ (.A(\out_reg[1] ),
    .B(\out_reg[0] ),
    .C(\out_reg[2] ),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .X(pad_vout));
 sky130_fd_sc_hd__dfrtp_2 _33_ (.CLK(clk),
    .D(pad_vctrl[0]),
    .RESET_B(rst_n),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Q(\ctrl_reg[0] ));
 sky130_fd_sc_hd__dfrtp_2 _34_ (.CLK(clk),
    .D(pad_vctrl[1]),
    .RESET_B(rst_n),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Q(\ctrl_reg[1] ));
 sky130_fd_sc_hd__dfrtp_2 _35_ (.CLK(clk),
    .D(pad_vctrl[2]),
    .RESET_B(rst_n),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Q(\ctrl_reg[2] ));
 sky130_fd_sc_hd__dfrtp_2 _36_ (.CLK(clk),
    .D(_00_),
    .RESET_B(rst_n),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Q(\out_reg[0] ));
 sky130_fd_sc_hd__dfrtp_2 _37_ (.CLK(clk),
    .D(_01_),
    .RESET_B(rst_n),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Q(\out_reg[1] ));
 sky130_fd_sc_hd__dfrtp_2 _38_ (.CLK(clk),
    .D(_02_),
    .RESET_B(rst_n),
    .VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .Q(\out_reg[2] ));
 sky130_fd_sc_hd__conb_1 _39_ (.VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .HI(vccd1));
 sky130_fd_sc_hd__conb_1 _40_ (.VGND(VGND),
    .VNB(VGND),
    .VPB(VPWR),
    .VPWR(VPWR),
    .LO(vssd1));
endmodule
