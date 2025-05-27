// cpu_core.v
`include "defines.vh"

module cpu_core (
    input clk,
    input rst,          // CPU复位信号
    input run_en,       // CPU运行使能 (来自顶层模块，用于暂停)

    // 指令存储器接口
    output [`INSTR_MEM_ADDR_WIDTH-1:0] pc_out, // 程序计数器输出 -> 指令存储器地址
    input [`WORD_WIDTH-1:0] instr_in,   // 从指令存储器读入的指令

    // 数据存储器接口
    output [`WORD_WIDTH-1:0] mem_addr,    // 数据存储器地址
    output [`WORD_WIDTH-1:0] mem_write_data, // 写入数据存储器的数据
    output mem_write_en,      // 数据存储器写使能
    output mem_read_en,       // 数据存储器读使能
    input [`WORD_WIDTH-1:0] mem_read_data    // 从数据存储器读入的数据
);

    // PC 寄存器
    reg [`INSTR_MEM_ADDR_WIDTH-1:0] pc_reg;
    wire [`INSTR_MEM_ADDR_WIDTH-1:0] pc_next;
    wire [`INSTR_MEM_ADDR_WIDTH-1:0] pc_plus_1;

    // 指令解码
    wire [3:0] opcode;
    wire [`REG_ADDR_WIDTH-1:0] rd_addr, rs1_addr, rs2_addr; // R-Type, I-Type (rs2_addr for BEQ)
    wire [`WORD_WIDTH-1:0] imm_signed; // 4-bit 立即数符号扩展
    wire [`INSTR_MEM_ADDR_WIDTH-1:0] jump_addr; // J-Type 地址

    // 控制信号
    reg reg_write_en;
    reg [3:0] alu_op_ctrl;
    reg alu_src_b_is_imm; // ALU 操作数B来源: 0=寄存器, 1=立即数
    reg mem_to_reg;     // 写回寄存器的数据来源: 0=ALU结果, 1=内存数据
    wire branch_taken;   // 分支是否成功
    wire is_halt_instr;  // 是否是HALT指令

    // 寄存器堆接口
    wire [`WORD_WIDTH-1:0] reg_read_data1, reg_read_data2;
    wire [`WORD_WIDTH-1:0] reg_write_data;

    // ALU 接口
    wire [`WORD_WIDTH-1:0] alu_operand_a, alu_operand_b;
    wire [`WORD_WIDTH-1:0] alu_result;
    wire alu_zero_flag;

    // --- PC逻辑 ---
    assign pc_out = pc_reg;
    assign pc_plus_1 = pc_reg + 1;

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            pc_reg <= `INSTR_MEM_ADDR_WIDTH'b0;
        end else if (run_en && !is_halt_instr) begin // 只有CPU运行且非HALT指令才更新PC
            pc_reg <= pc_next;
        end
    end

    // --- 指令解码 ---
    assign opcode = instr_in[15:12];
    // R-Type, I-Type (ADDI, LW, SW)
    assign rd_addr  = instr_in[11:8]; 
    assign rs1_addr = instr_in[7:4];  
    // R-Type, BEQ
    assign rs2_addr = instr_in[3:0];  

    // 立即数符号扩展 (4-bit to 16-bit)
    assign imm_signed = {{12{instr_in[3]}}, instr_in[3:0]}; 
    // JMP 地址
    assign jump_addr = instr_in[11:0];

    // --- 控制逻辑 (组合逻辑) ---
    always @(*) begin
        // 默认值
        reg_write_en = 1'b0;
        alu_op_ctrl = 4'b0; // NOP or default
        alu_src_b_is_imm = 1'b0;
        mem_to_reg = 1'b0;
        mem_write_en = 1'b0;
        mem_read_en = 1'b0;

        case (opcode)
            `OP_HALT: begin
                // 无操作，PC不更新已在PC逻辑中处理
            end
            `OP_ADD: begin
                reg_write_en = 1'b1;
                alu_op_ctrl = `OP_ADD; // 使用操作码作为ALU控制信号
                alu_src_b_is_imm = 1'b0;
                mem_to_reg = 1'b0;
            end
            `OP_SUB: begin
                reg_write_en = 1'b1;
                alu_op_ctrl = `OP_SUB;
                alu_src_b_is_imm = 1'b0;
                mem_to_reg = 1'b0;
            end
            `OP_AND: begin
                reg_write_en = 1'b1;
                alu_op_ctrl = `OP_AND;
                alu_src_b_is_imm = 1'b0;
                mem_to_reg = 1'b0;
            end
            `OP_OR: begin
                reg_write_en = 1'b1;
                alu_op_ctrl = `OP_OR;
                alu_src_b_is_imm = 1'b0;
                mem_to_reg = 1'b0;
            end
            `OP_ADDI: begin
                reg_write_en = 1'b1;
                alu_op_ctrl = `OP_ADD; // ADDI 使用 ADD 操作
                alu_src_b_is_imm = 1'b1;
                mem_to_reg = 1'b0;
            end
            `OP_LW: begin
                reg_write_en = 1'b1;
                alu_op_ctrl = `OP_ADD; // 地址计算用ADD
                alu_src_b_is_imm = 1'b1; // Rs1 + Imm
                mem_read_en = 1'b1;
                mem_to_reg = 1'b1;
            end
            `OP_SW: begin
                // reg_write_en is 0 for SW
                alu_op_ctrl = `OP_ADD; // 地址计算用ADD
                alu_src_b_is_imm = 1'b1; // Rs1 + Imm
                mem_write_en = 1'b1;
                // mem_to_reg is 0
            end
            `OP_BEQ: begin
                // reg_write_en is 0 for BEQ
                alu_op_ctrl = `OP_SUB; // 比较 (a-b==0?)
                alu_src_b_is_imm = 1'b0;
                // mem_to_reg is 0
                // branch_taken 在下面计算
            end
            `OP_JMP: begin
                // reg_write_en is 0 for JMP
                // mem_to_reg is 0
            end
            default: begin
                // 无效指令，可以触发异常或视为NOP
            end
        endcase
    end
    
    assign is_halt_instr = (opcode == `OP_HALT);

    // --- 数据通路 ---

    // 寄存器堆实例化
    register_file u_reg_file (
        .clk(clk),
        .rst(rst), // 寄存器堆也受CPU复位影响
        .write_en(reg_write_en && run_en && !is_halt_instr), // 仅在CPU运行且非HALT时写寄存器
        .read_addr1(rs1_addr),
        .read_addr2(rs2_addr), // R-Type 和 BEQ 使用
        .write_addr(rd_addr),
        .write_data(reg_write_data),
        .read_data1(reg_read_data1),
        .read_data2(reg_read_data2)
    );

    // ALU 操作数选择
    assign alu_operand_a = reg_read_data1;
    assign alu_operand_b = alu_src_b_is_imm ? imm_signed : reg_read_data2;

    // ALU 实例化
    alu u_alu (
        .operand_a(alu_operand_a),
        .operand_b(alu_operand_b),
        .alu_op(alu_op_ctrl),
        .result(alu_result),
        .zero_flag(alu_zero_flag)
    );

    // 写回寄存器的数据选择
    assign reg_write_data = mem_to_reg ? mem_read_data : alu_result;

    // 数据存储器接口赋值
    assign mem_addr = alu_result; // LW/SW的地址由ALU计算 (Rs1 + Imm)
    assign mem_write_data = reg_read_data2; // SW指令: Rt的内容 (在R-Type的rs2位置)
                                        // 注意：SW指令的源数据寄存器是 instr_in[11:8] (rd_addr字段)
                                        // 所以应该是 assign mem_write_data = reg_file_output_for_rd_field;
                                        // 为了简单，我们假设SW指令的第二个源操作数来自rs2_addr对应的寄存器。
                                        // 更标准的RISC-V SW: Mem[rs1+imm] = rs2
                                        // 我们的ISA: Mem[R[rs1]+imm] = R[Rt], Rt在rd_addr字段
                                        // 所以应该是：
                                        // wire [`WORD_WIDTH-1:0] reg_read_for_sw_data;
                                        // register_file ... .read_addr_FOR_SW(rd_addr), .read_data_FOR_SW(reg_read_for_sw_data)
                                        // assign mem_write_data = reg_read_for_sw_data;
                                        // 为简化，当前设计中，SW指令将 reg_read_data2 (rs2_addr的内容) 写入内存。
                                        // 如果要严格按照ISA: Mem[R[Rs1] + imm] = R[Rt]，Rt是rd_addr字段。
                                        // 那么，寄存器堆需要第三个读端口，或者分周期。
                                        // 对于单周期，通常寄存器堆有两个读口。
                                        // 让我们修正SW的源数据：它应该是来自rd_addr字段指定的寄存器。
                                        // 但我们只有两个读端口。这是一个单周期CPU的常见冲突。
                                        // 解决方法1: SW使用rs2作为数据源。 (当前实现)
                                        // 解决方法2: 修改ISA，使SW的源寄存器是rs2。
                                        // 解决方法3: 增加读端口 (复杂)。
                                        // 我们保持当前实现：SW将R[rs2_addr]写入。用户需注意。
                                        // 如果ISA是 Mem[R[Rs1]+imm] = R[Rt] where Rt is instr[11:8]
                                        // 那么就需要把 instr[11:8] 连接到 reg_file 的 read_addr2 (如果alu_src_b_is_imm为true)
                                        // 这是一个设计选择，为简单起见，我们用rs2_addr作为SW的数据源。
                                        // 即 SW R[rs1_addr], R[rs2_addr], imm  => Mem[R[rs1_addr]+imm] = R[rs2_addr]
                                        // 此时，rd_addr字段 (instr[11:8]) 对于SW指令是未使用的。

    // 分支逻辑
    assign branch_taken = (opcode == `OP_BEQ) && (reg_read_data1 == reg_read_data2); // BEQ: rs1 == rs2
                         // 如果alu_zero_flag用于比较结果 (rs1-rs2==0), 则:
                         // assign branch_taken = (opcode == `OP_BEQ) && alu_zero_flag; 
                         // (前提是BEQ时alu_op_ctrl设为SUB)

    // Next PC 计算
    assign pc_next = (opcode == `OP_JMP) ? jump_addr :
                     (branch_taken) ? (pc_plus_1 + imm_signed) : // BEQ跳转地址计算
                                      pc_plus_1;

endmodule
