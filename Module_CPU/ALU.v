
//ALU（算术逻辑单元）：用于逻辑指令计算和跳转指令比较

module ALU(
    input [2:0] ALUOp,  // ALU操作控制码
    input [15:0] A,     //操作数1
    input [15:0] B,     //操作数2
    output reg [15:0] ALUResult,   //ALU运算结果
    output reg zero    // 运算结果result的标志，result为0输出1，否则输出0
);
    // 进行ALU计算
    // 0：add, 1：sub, 2：and, 3：or 4:beq 5:ble
    always @(*) begin
        case(ALUOp)
            3'b000 : ALUResult = A + B;
            3'b001 : ALUResult = A - B;
            3'b010 : ALUResult = A & B;
            3'b011 : ALUResult = A | B;
            3'b100 : ALUResult = (A == B);
            3'b101 : ALUResult = (A <= B);
            default : ALUResult = 16'b0;
        endcase

        //设置zero
            if (ALUResult) zero = 0;
            else zero = 1;
    end

endmodule