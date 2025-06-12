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
    input RESET,    //cpu执行,低电平有效
    input wait_transport,   //等待传输信号,低电平有效
    input uart_rx_pin,    // UART串行数据输入

    output  led1,     //led灯显示
    output  led2,
    output  led3,
    output  led4,    // led4指示CPU暂停状态(1=暂停/加载, 0=加载完成/运行)

    output  dig1,    //数码管从左到右为1-6
    output  dig2,
    output  dig3,
    output  dig4, 
    output  dig5, 
    output  dig6, 
    output [6:0] out 
    );

    //  1. 定义状态，用于处理字节接收和拼接
    localparam S_WAIT_COUNT    = 4'b0001; // 等待接收指令总数的低字节 1
    localparam S_WAIT_COUNT_MSB    = 4'b0010; // 等待接收指令总数的高字节 2
    localparam S_LOADING_INSTR_LSB = 4'b0011; // 等待接收指令的低字节 3
    localparam S_LOADING_INSTR_MSB = 4'b0100; // 等待接收指令的高字节 4
    localparam S_LOAD_DONE         = 4'b0101; // 加载完成，等待启动 5
    localparam S_RUNNING           = 4'b0110; // CPU运行 6

    // 2. 添加状态寄存器、计数器和临时字节存储器
    reg [3:0] state_reg;
    reg [7:0] temp_lsb_reg; // 用于暂存接收到的低字节
    reg [15:0] expected_instr_count_reg;    // 期望的指令总数
    reg [15:0] received_instr_count_reg;    //  已接收的指令数

    // UART接口信号
    wire [7:0] uart_received_byte; // UART现在输出8位字节
    wire uart_byte_valid;   //UART数据有效信号

    // 指令存储器接口
    wire [15:0] MachineCodeData;   //拼接后的机器码数据
    reg [15:0] MachineCodeAddress;    //机器码对应的地址
    
    //内部信号
    wire cpu_rst; // CPU核心的实际复位信号
    wire cpu_run_enable;        // CPU运行使能
    wire instr_mem_write_enable; // 指令存储器实际写使能

    // 相关变量
    wire [3:0] op;
    wire [3:0] rs;
    wire [3:0] rt;
    wire [3:0] rd;

    wire [15:0] ReadData1;
    wire [15:0] ReadData2;
    wire [15:0] WriteData;
    wire [15:0] DataOut;
    wire [15:0] currentAddress;
    wire [15:0] result;
    wire [15:0] DataFromROM;
    wire [15:0] ROMDataAddress;    //ROM数据地址
    
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

    wire led1_from_DM;
    wire led2_from_DM;
    wire led3_from_DM;
    wire led4_from_DM;

    // 3. 拼接逻辑
    assign MachineCodeData = {uart_received_byte, temp_lsb_reg}; // MSB在高位，LSB在低位

    // 4. 根据状态控制LED4和CPU运行
    assign led1 = ((state_reg == S_LOAD_DONE) || (state_reg == S_RUNNING)) ? led1_from_DM : 1'b0;
    assign led2 = ((state_reg == S_LOAD_DONE) || (state_reg == S_RUNNING)) ? led2_from_DM : 1'b0;
    assign led3 = ((state_reg == S_LOAD_DONE) || (state_reg == S_RUNNING)) ? led3_from_DM : 1'b0;
    assign led4 = ((state_reg == S_LOAD_DONE) || (state_reg == S_RUNNING)) ? led4_from_DM : 1'b1;

    // assign led3 = (state_reg == S_RUNNING)?  1'b1 : 1'b0;
    assign cpu_run_enable = (state_reg == S_RUNNING);
    assign cpu_rst = RESET || !((state_reg == S_LOAD_DONE) || (state_reg == S_RUNNING));

    // 5. 状态机逻辑 (核心改动)
    initial begin
        state_reg <= S_WAIT_COUNT;
        expected_instr_count_reg <= 0;
        received_instr_count_reg <= 0;
        MachineCodeAddress <= 0;
        // ... 其他寄存器初始化
    end

    always @(posedge CLK or negedge RESET) begin
        if (!RESET) begin
            state_reg <= S_RUNNING;
        end
        else if(wait_transport == 0)
            state_reg <= S_WAIT_COUNT;
        else begin
            case (state_reg)
                S_WAIT_COUNT: begin
                    if (uart_byte_valid) begin
                        temp_lsb_reg <= uart_received_byte;
                        state_reg <= S_WAIT_COUNT_MSB;
                    end
                end
                
                S_WAIT_COUNT_MSB: begin
                    if (uart_byte_valid) begin
                        expected_instr_count_reg <= MachineCodeData; // 拼接成16位计数值
                        received_instr_count_reg <= 0;
                        MachineCodeAddress <= 0;
                        if (MachineCodeData == 0) begin
                            state_reg <= S_LOAD_DONE;
                        end else begin
                            state_reg <= S_LOADING_INSTR_LSB;
                        end
                    end
                end

                S_LOADING_INSTR_LSB: begin
                    if (uart_byte_valid) begin
                        temp_lsb_reg <= uart_received_byte;
                        state_reg <= S_LOADING_INSTR_MSB;
                    end
                end

                S_LOADING_INSTR_MSB: begin
                    if (uart_byte_valid) begin
                        // 此时MachineCodeData是完整的16位指令，可以写入内存
                        // instr_mem_write_enable 会在此状态且uart_byte_valid时为高
                        
                        received_instr_count_reg <= received_instr_count_reg + 1;
                        MachineCodeAddress <= MachineCodeAddress + 1;

                        if ((received_instr_count_reg + 1) == expected_instr_count_reg) begin
                            state_reg <= S_LOAD_DONE;
                        end else begin
                            state_reg <= S_LOADING_INSTR_LSB; // 返回等待下一条指令的低字节
                        end
                    end
                end
                
                S_LOAD_DONE: begin

                end
                
                S_RUNNING: begin
                    // else if(!wait_transport)
                    //     state_reg <= S_WAIT_COUNT;
                end
                // default: state_reg <= S_WAIT_COUNT;
            endcase
        end
    end



    // 6. 指令存储器写使能逻辑
    // 只有在接收到一条指令的高字节时，才产生写使能脉冲
    assign instr_mem_write_enable = (state_reg == S_LOADING_INSTR_MSB) && uart_byte_valid;



// 各模块实例化
    // uart_rx
    uart_rx u_uart_rx (
        .sys_clk(CLK),
        .sys_rst_n(RESET), // UART模块可以被主复位按钮复位
        .rx(uart_rx_pin),
        .po_data(uart_received_byte),
        .po_flag(uart_byte_valid)
    );

    // 控制器
    // ControlUnit cu(op, zero, m2reg, PCsrc, wmem,memc, ALUOp, alucsrc, wreg, jal);
    ControlUnit cu(op, zero, m2reg, PCsrc, wmem, memc, ALUOp, alucsrc, wreg);


    // PC：CLK上升沿触发，更改指令地址
    PC pc(CLK, RESET, cpu_run_enable,  newAddress, currentAddress);

    // InstructionMemory：储存指令，分割指令
    InstructionMemory im(CLK, instr_mem_write_enable, MachineCodeAddress, MachineCodeData, ROMDataAddress, currentAddress, op, rs, rt, rd, instruction, DataFromROM);
    
    // ImmExt: 用于immediate的扩展
    ImmExt ImmE(instruction, immExt);

    //RegisterFile：储存寄存器组，并根据地址对寄存器组进行读写
    RegisterFile rf(CLK, RESET, wreg && cpu_run_enable, rs, rt, rd, WriteData, ReadData1, ReadData2);

    //ALU（算术逻辑单元）：用于逻辑指令计算和跳转指令比较
    ALU alu(ALUOp, ReadData1, B,  result, zero);

    // DataMemory：用于内存存储，内存读写
    DataMemory DM(CLK, RESET, wmem && cpu_run_enable, result, ReadData2, memc ,DataFromROM, DataOut, led1_from_DM, led2_from_DM, led3_from_DM, led4_from_DM, ROMDataAddress, dig1, dig2, dig3, dig4, dig5, dig6, out);

    assign currentAddress_2 = currentAddress + 2;
    assign currentAddress_immediate = currentAddress + immExt;

    // 选择ALU的操作数 B 是立即数还是寄存器的数据
    Multiplexer21 m21(alucsrc, ReadData2, immExt, B);
    

    // 为寄存器组选择数据来源，ALU的结果或内存的数据或currentAddress_2或左移8位后的数据
    Multiplexer41 m41(m2reg, result, DataOut, currentAddress_2, immExt, WriteData);

    // 选择写回PC的数据来源，PC+2 或 PC+immExt 或 result
    Multiplexer31 m31(PCsrc, currentAddress_2, currentAddress_immediate, result, newAddress);





endmodule
