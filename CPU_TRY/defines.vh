// defines.vh
// 定义指令操作码和功能码

// Opcodes
`define OP_HALT  4'b0000 // 停止
`define OP_ADD   4'b0001 // R[Rd] = R[Rs1] + R[Rs2]
`define OP_SUB   4'b0010 // R[Rd] = R[Rs1] - R[Rs2]
`define OP_AND   4'b0011 // R[Rd] = R[Rs1] & R[Rs2]
`define OP_OR    4'b0100 // R[Rd] = R[Rs1] | R[Rs2]
// SLT (Set Less Than) 可以作为R-Type的扩展
// `define OP_SLT   4'b0101 

`define OP_ADDI  4'b1001 // R[Rd] = R[Rs1] + Imm
`define OP_LW    4'b1011 // R[Rd] = Mem[R[Rs1] + Imm]
`define OP_SW    4'b1100 // Mem[R[Rs1] + Imm] = R[Rt] (Rt is in Rd field for SW)
`define OP_BEQ   4'b1101 // if (R[Rs1] == R[Rs2]) PC = PC + 1 + Imm

`define OP_JMP   4'b1111 // PC = Address

// 指令字段提取辅助宏 (示例，实际解码在CPU控制逻辑中)
// `define OPCODE(instr) instr[15:12]
// `define RD(instr)   instr[11:8]
// `define RS1(instr)  instr[7:4]
// `define RS2(instr)  instr[3:0] // For R-Type
// `define IMM4(instr) instr[3:0]  // For I-Type (ALU, LW/SW offset, BEQ offset)
// `define ADDR12(instr) instr[11:0] // For J-Type

// PC 和内存地址宽度
`define PC_WIDTH 12
`define INSTR_MEM_ADDR_WIDTH `PC_WIDTH
`define INSTR_MEM_DEPTH (1 << `INSTR_MEM_ADDR_WIDTH) // 4096

`define DATA_MEM_ADDR_WIDTH 8 // 数据存储器地址宽度 (例如 256 字)
`define DATA_MEM_DEPTH (1 << `DATA_MEM_ADDR_WIDTH) // 256

`define WORD_WIDTH 16
`define REG_ADDR_WIDTH 4
`define NUM_REGS (1 << `REG_ADDR_WIDTH) // 16个寄存器

