// top_module.v
`include "defines.vh"

module top_module1 (
    input CLK,
    input RESET,  // 外部物理复位/启动按钮
    input uart_rx_pin,    // UART串行数据输入

    output led_cpu_paused // LED指示CPU暂停状态 (1=暂停/加载, 0=加载完成/运行)
);

    // 1. 定义状态
    localparam S_WAIT_COUNT      = 3'b001; // 状态: 等待接收指令总数 (LED亮)
    localparam S_LOADING_INSTR   = 3'b010; // 状态: 加载指令 (LED亮)
    localparam S_LOAD_DONE       = 3'b011; // 状态: 加载完成，等待启动 (LED灭)
    localparam S_RUNNING         = 3'b100; // 状态: CPU运行 (LED灭)

    // 2. 添加状态寄存器和计数器
    reg [2:0] state_reg;
    reg [`WORD_WIDTH-1:0] expected_instr_count_reg; // 期望接收的指令总数 (最大 2^16-1, 但实际受限于指令内存大小)
    reg [`WORD_WIDTH-1:0] received_instr_count_reg; // 已接收的指令数量

    // 内部信号
    wire cpu_rst; // CPU核心的实际复位信号
    wire cpu_run_enable;        // CPU运行使能
    wire instr_mem_write_enable; // 指令存储器实际写使能

    // UART接口信号
    wire [`WORD_WIDTH-1:0] uart_received_data;
    wire uart_byte_valid;

    // 指令存储器接口
    reg [`INSTR_MEM_ADDR_WIDTH-1:0] MachineCodeAddress; // 当前要写入的指令存储器地址
    wire [`WORD_WIDTH-1:0] instr_from_mem;

    // CPU核心接口
    wire [`INSTR_MEM_ADDR_WIDTH-1:0] pc_from_cpu;
    // ... (其他CPU到数据内存的信号声明与之前类似)
    wire [`WORD_WIDTH-1:0] data_mem_addr_from_cpu;
    wire [`WORD_WIDTH-1:0] data_mem_write_data_from_cpu;
    wire data_mem_write_en_from_cpu;
    wire data_mem_read_en_from_cpu;
    wire [`WORD_WIDTH-1:0] data_from_data_mem;

    // 3. 根据状态控制LED和CPU运行/复位
    assign led_cpu_paused = (state_reg == S_WAIT_COUNT) || (state_reg == S_LOADING_INSTR);
    assign cpu_run_enable = (state_reg == S_RUNNING);
    assign cpu_rst = RESET && ((state_reg == S_LOAD_DONE) || (state_reg == S_RUNNING));

    // 4. 状态机逻辑
    initial begin
        state_reg <= S_WAIT_COUNT;
        expected_instr_count_reg <= 0;
        received_instr_count_reg <= 0;
        MachineCodeAddress <= 0;
    end

    always @(posedge CLK) begin // 使用同步复位或异步复位RESET取决于设计需求
                           // 这里假设RESET主要用于状态转换和CPU核复位，FSM主要由CLK驱动
        case (state_reg)
            S_WAIT_COUNT: begin
                if (uart_byte_valid) begin
                    expected_instr_count_reg <= uart_received_data;
                    received_instr_count_reg <= 0; // 清零已接收计数
                    MachineCodeAddress <= 0; // 指令从地址0开始存
                    if (uart_received_data == 0) begin // 如果期望数量为0
                        state_reg <= S_LOAD_DONE;
                    end else begin
                        state_reg <= S_LOADING_INSTR;
                    end
                end
            end

            S_LOADING_INSTR: begin
                if (uart_byte_valid) begin
                    // 指令写入已由 instr_mem_write_enable 控制
                    // 更新计数器和下一个写地址
                    received_instr_count_reg <= received_instr_count_reg + 1;
                    MachineCodeAddress <= MachineCodeAddress + 1;

                    if ((received_instr_count_reg + 1) == expected_instr_count_reg) begin
                        state_reg <= S_LOAD_DONE;
                    end
                end
            end

            S_LOAD_DONE: begin
                if (RESET) begin // 只有在加载完成后，复位按钮才启动CPU
                    state_reg <= S_RUNNING;
                end
            end

            S_RUNNING: begin
                if (RESET) begin
                    // CPU核心已通过 cpu_rst 复位，保持运行状态
                    // PC会回到0，重新执行
                end
            end
            default: state_reg <= S_WAIT_COUNT;
        endcase
        
        // 如果希望RESET能重置整个加载过程 (回到S_WAIT_COUNT)
        // if (RESET && (state_reg == S_WAIT_COUNT || state_reg == S_LOADING_INSTR)) begin
        //     state_reg <= S_WAIT_COUNT;
        //     expected_instr_count_reg <= 0;
        //     received_instr_count_reg <= 0;
        //     MachineCodeAddress <= 0;
        // end
    end

    // 5. 指令存储器的写使能逻辑
    // 只有在加载指令状态且UART有新数据时，才写入内存
    assign instr_mem_write_enable = (state_reg == S_LOADING_INSTR) && uart_byte_valid;

    // --- 模块实例化 ---

    uart_rx u_uart_rx (
        .CLK(CLK),
        .rst(RESET), // UART模块可以被主复位按钮复位
        .rx_in(uart_rx_pin),
        .data_out(uart_received_data),
        .data_valid(uart_byte_valid)
    );

    instruction_memory u_instr_mem (
        .CLK(CLK),
        .write_addr(MachineCodeAddress),
        .write_data(uart_received_data),
        .write_en(instr_mem_write_enable),
        .read_addr(pc_from_cpu),
        .read_data(instr_from_mem)
    );

    cpu_core u_cpu (
        .CLK(CLK),
        .rst(cpu_rst), // 使用受控的复位信号
        .run_en(cpu_run_enable),
        .pc_out(pc_from_cpu),
        .instr_in(instr_from_mem),
        .mem_addr(data_mem_addr_from_cpu),
        .mem_write_data(data_mem_write_data_from_cpu),
        .mem_write_en(data_mem_write_en_from_cpu),
        .mem_read_en(data_mem_read_en_from_cpu),
        .mem_read_data(data_from_data_mem)
    );

    data_memory u_data_mem (
        .CLK(CLK),
        .addr(data_mem_addr_from_cpu),
        .write_data(data_mem_write_data_from_cpu),
        .mem_write_en(data_mem_write_en_from_cpu && cpu_run_enable),
        .mem_read_en(data_mem_read_en_from_cpu && cpu_run_enable),
        .read_data(data_from_data_mem)
    );

endmodule