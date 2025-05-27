// top_module.v
`include "defines.vh"

module top_module (
    input clk,            // 系统时钟
    input rst_button_in,  // 外部物理复位/启动按钮 (低电平有效或高电平有效，假设高电平有效)
    input uart_rx_pin,    // UART串行数据输入

    output led_cpu_paused // LED指示CPU暂停状态 (1=暂停, 0=运行)
);

    // 内部信号
    wire cpu_core_rst;       // CPU核心的复位信号
    reg cpu_run_enable_reg; // 控制CPU是否运行的使能信号
    reg cpu_paused_state_reg; // 1: CPU暂停/加载指令, 0: CPU运行

    // UART接口信号
    wire [`WORD_WIDTH-1:0] uart_received_data;
    wire uart_data_valid_pulse;

    // 指令存储器接口
    reg [`INSTR_MEM_ADDR_WIDTH-1:0] instr_mem_write_address_reg;
    wire instr_mem_write_enable;
    wire [`WORD_WIDTH-1:0] instr_from_mem; // 从指令存储器读出的指令

    // CPU核心接口
    wire [`INSTR_MEM_ADDR_WIDTH-1:0] pc_from_cpu;
    wire [`WORD_WIDTH-1:0] data_mem_addr_from_cpu;
    wire [`WORD_WIDTH-1:0] data_mem_write_data_from_cpu;
    wire data_mem_write_en_from_cpu;
    wire data_mem_read_en_from_cpu;
    wire [`WORD_WIDTH-1:0] data_from_data_mem;


    // 将暂停状态直接输出到LED
    assign led_cpu_paused = cpu_paused_state_reg;

    // CPU核心的复位信号直接连接到外部按钮
    // (如果按钮是低电平有效，rst_button_in需要取反或用防抖电路)
    assign cpu_core_rst = rst_button_in; 

    // CPU运行使能逻辑
    assign instr_mem_write_enable = cpu_paused_state_reg && uart_data_valid_pulse;

    // 初始化状态
    initial begin
        cpu_paused_state_reg = 1'b1; // 上电后CPU暂停，等待加载
        cpu_run_enable_reg = 1'b0;   // CPU不运行
        instr_mem_write_address_reg = `INSTR_MEM_ADDR_WIDTH'b0;
    end

    // 状态控制逻辑: CPU暂停/运行切换
    // 使用 rst_button_in 作为状态切换和复位信号
    always @(posedge clk or posedge rst_button_in) begin // 按钮按下会触发
        if (rst_button_in) begin
            // 任何时候按下按钮，都重置指令写入地址
            instr_mem_write_address_reg <= `INSTR_MEM_ADDR_WIDTH'b0; 
            
            if (cpu_paused_state_reg == 1'b1) begin
                // 如果当前是暂停状态，按下按钮则切换到运行状态
                cpu_paused_state_reg <= 1'b0; // LED将熄灭
                cpu_run_enable_reg <= 1'b1;   // CPU开始运行
                                             // cpu_core_rst (连接到rst_button_in) 会复位CPU内部PC
            end else begin
                // 如果当前是运行状态，按下按钮则仅复位CPU (PC到0)
                // cpu_paused_state_reg 保持 1'b0
                // cpu_run_enable_reg 保持 1'b1
                // cpu_core_rst 会复位CPU内部PC
            end
        end
    end

    // 指令加载逻辑: 当CPU暂停且UART有新数据时，写入指令存储器
    always @(posedge clk) begin
        if (cpu_paused_state_reg && uart_data_valid_pulse) begin
            // 指令已通过 instr_mem_write_enable 写入指令存储器模块
            // 更新下一个写入地址
            instr_mem_write_address_reg <= instr_mem_write_address_reg + 1;
        end
    end

    // --- 模块实例化 ---

    // UART接收模块
    uart_rx u_uart_rx (
        .clk(clk),
        .rst(cpu_core_rst), // UART模块也受主复位信号影响
        .rx_in(uart_rx_pin),
        .data_out(uart_received_data),
        .data_valid(uart_data_valid_pulse)
    );

    // 指令存储器
    instruction_memory u_instr_mem (
        .clk(clk),
        .write_addr(instr_mem_write_address_reg),
        .write_data(uart_received_data),
        .write_en(instr_mem_write_enable),
        .read_addr(pc_from_cpu), // CPU的PC作为读地址
        .read_data(instr_from_mem)
    );

    // CPU核心
    cpu_core u_cpu (
        .clk(clk),
        .rst(cpu_core_rst),
        .run_en(cpu_run_enable_reg),
        .pc_out(pc_from_cpu),
        .instr_in(instr_from_mem),
        .mem_addr(data_mem_addr_from_cpu),
        .mem_write_data(data_mem_write_data_from_cpu),
        .mem_write_en(data_mem_write_en_from_cpu),
        .mem_read_en(data_mem_read_en_from_cpu),
        .mem_read_data(data_from_data_mem)
    );

    // 数据存储器
    data_memory u_data_mem (
        .clk(clk),
        .addr(data_mem_addr_from_cpu),
        .write_data(data_mem_write_data_from_cpu),
        .mem_write_en(data_mem_write_en_from_cpu && cpu_run_enable_reg), // 仅在CPU运行时写真内存
        .mem_read_en(data_mem_read_en_from_cpu && cpu_run_enable_reg),  // 仅在CPU运行时读真内存
        .read_data(data_from_data_mem)
    );

endmodule
