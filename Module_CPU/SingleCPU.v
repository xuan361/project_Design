`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date:    23:43:17 05/02/2017 
// Design Name: 
// Module Name:    SingleCPU 
// Project Name: 
// Target Devices: 
// Tool versions: 
// Description: 
//
// Dependencies: 
//
// Revision: 
// Revision 0.01 - File Created
// Additional Comments: 
//
//////////////////////////////////////////////////////////////////////////////////
// `include "D:\\learn\\Git\\testgit\\Module_CPU\\ALU.v"

module SingleCPU(
    input CLK,
    input RESET,

    output [3:0] op,
    output [3:0] rs,
    output [3:0] rt,
    output [3:0] rd,

    output [15:0] ReadData1,
    output [15:0] ReadData2,
    output [15:0] WriteData,
    output [15:0] DataOut,
    output [15:0] currentAddress,
    output [15:0] result
    );

    // 各种临时变量
    wire [2:0] ALUOp; 
    wire[1:0]  m2reg;
    wire wmem, alucsrc, wreg, memc;  // 控制信号 
    wire[1:0] PCsrc;
    wire [15:0] newAddress;
    wire [15:0] currentAddress_2, currentAddress_immediate;
    wire [15:0] B;
    wire [15:0] immExt; 
    wire [15:0] instruction;
    wire [15:0] back_regiser;


// 各模块实例化
    // 控制器
    // ControlUnit cu(op, zero, m2reg, PCsrc, wmem,memc, ALUOp, alucsrc, wreg, jal);
    ControlUnit cu(op, zero, m2reg, PCsrc, wmem,memc, ALUOp, alucsrc, wreg);


    // PC：CLK上升沿触发，更改指令地址
    PC pc(CLK, RESET, newAddress, currentAddress);

    // InstructionMemory：储存指令，分割指令
    InstructionMemory im(currentAddress, op, rs, rt, rd, instruction);
    
    // ImmExt: 用于immediate的扩展
    ImmExt ImmE(instruction, immExt);

    //RegisterFile：储存寄存器组，并根据地址对寄存器组进行读写
    RegisterFile rf(CLK, RESET, wreg, rs, rt, rd, WriteData, ReadData1, ReadData2);

    //ALU（算术逻辑单元）：用于逻辑指令计算和跳转指令比较
    ALU alu(ALUOp, ReadData1, B,  result, zero);



    // DataMemory：用于内存存储，内存读写
    DataMemory DM(CLK, RESET, wmem, result, ReadData2, memc, DataOut);

    assign currentAddress_2 = currentAddress + 2;
    assign currentAddress_immediate = currentAddress + immExt;

    // 选择ALU的操作数 B 是立即数还是寄存器的数据
    Multiplexer21 m21(alucsrc, ReadData2, immExt, B);
    
    // // 选择写回寄存器组的数据来源，ALU的结果或存储器的数据
    // Multiplexer21 m21_1(m2reg, result, DataOut, back_regiser);

    // 为寄存器组选择数据来源，ALU的结果或内存的数据或currentAddress_2或左移8位后的数据
    Multiplexer41 m41(m2reg, result, DataOut, currentAddress_2, immExt, WriteData);

    // 选择写回PC的数据来源，PC+2 或 PC+immExt 或 result
    Multiplexer31 m31(PCsrc, currentAddress_2, currentAddress_immediate, result, newAddress);





endmodule
