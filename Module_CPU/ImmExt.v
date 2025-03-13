
// ImmExt: 用于immediate的扩展

module ImmExt(
    input [3:0] imm,   //立即数
    output [15:0] immExt    //扩展后的立即数
);

// 进行扩展
//将高12位全补为1或0（取决于符号位）
assign immExt[15:4] = imm[3] ? 12'b1111_1111_1111 : 0;
assign immExt[3:0] = imm;

endmodule
