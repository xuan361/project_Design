`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2025/03/20 21:15:51
// Design Name: 
// Module Name: ControlUnit_tb
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


`timescale 1ns / 1ps

module ControlUnit_tb();

    // 测试信号定义
    reg [3:0] op;          // 操作码输入
    reg zero;              // ALU zero 输出

    // 控制信号输出
    wire m2reg;            // 读取存储器的数据是否需要写回寄存器
    wire [1:0] PCsrc;      // 控制程序计数器的更新来源
    wire wmem;             // 控制存储器的写操作
    wire memc;             // 控制写字节数（1字节或2字节）
    wire [2:0] ALUOp;      // 控制 ALU 的操作类型
    wire alucsrc;          // 控制 ALU 输入来源（寄存器或立即数）
    wire wreg;             // 控制寄存器写操作
    wire jal;              // 控制跳转指令的跳转类型

    // 实例化 ControlUnit 模块
    ControlUnit CU (
        .op(op),
        .zero(zero),
        .m2reg(m2reg),
        .PCsrc(PCsrc),
        .wmem(wmem),
        .memc(memc),
        .ALUOp(ALUOp),
        .alucsrc(alucsrc),
        .wreg(wreg),
        .jal(jal)
    );

    // 初始化信号
    initial begin
        // 初始化信号
        op = 4'b0000;   // 默认操作码
        zero = 1'b0;    // 默认 ALU zero 输出为 0

        // // 打印输出的控制信号
        // $monitor("Time = %0d, op = %b, zero = %b, m2reg = %b, PCsrc = %b, wmem = %b, memc = %b, ALUOp = %b, alucsrc = %b, wreg = %b, jal = %b",
        //          $time, op, zero, m2reg, PCsrc, wmem, memc, ALUOp, alucsrc, wreg, jal);
        
        // 运行不同的操作码测试
        #10 op = 4'b0000;  // 测试 jal
        #10 op = 4'b0001;  // 测试 jalr
        #10 op = 4'b0010;  // 测试 beq
        #10 op = 4'b0011;  // 测试 ble
        #10 op = 4'b0100;  // 测试 lb
        #10 op = 4'b0101;  // 测试 lw
        #10 op = 4'b0110;  // 测试 sb
        #10 op = 4'b0111;  // 测试 sw
        #10 op = 4'b1000;  // 测试 add
        #10 op = 4'b1001;  // 测试 sub
        #10 op = 4'b1010;  // 测试 and
        #10 op = 4'b1011;  // 测试 or
        #10 op = 4'b1100;  // 测试 addi
        #10 op = 4'b1101;  // 测试 subi
        #10 op = 4'b1110;  // 测试 andi
        #10 op = 4'b1111;  // 测试 ori

        // 测试 zero 信号的影响
        #10 zero = 1'b1;   // 设置 zero 为 1，测试 beq 和 ble 条件
        #10 op = 4'b0000;  // 测试 jal
        #10 op = 4'b0001;  // 测试 jalr
        #10 op = 4'b0010;  // 测试 beq
        #10 op = 4'b0011;  // 测试 ble
        #10 op = 4'b0100;  // 测试 lb
        #10 op = 4'b0101;  // 测试 lw
        #10 op = 4'b0110;  // 测试 sb
        #10 op = 4'b0111;  // 测试 sw
        #10 op = 4'b1000;  // 测试 add
        #10 op = 4'b1001;  // 测试 sub
        #10 op = 4'b1010;  // 测试 and
        #10 op = 4'b1011;  // 测试 or
        #10 op = 4'b1100;  // 测试 addi
        #10 op = 4'b1101;  // 测试 subi
        #10 op = 4'b1110;  // 测试 andi
        #10 op = 4'b1111;  // 测试 ori


        #10 $finish;        // 结束仿真
    end

endmodule

