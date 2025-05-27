// top_module.v (修改版，支持字节组装)
`include "defines.vh"

module top_module (
    input CLK,
    input RESET,
    input uart_rx_pin,
    output led_cpu_paused
);

    // 1. 定义新的状态机，用于处理字节接收和拼接
    localparam S_WAIT_COUNT    = 4'b0001; // 等待接收指令总数的低字节
    localparam S_WAIT_COUNT_MSB    = 4'b0010; // 等待接收指令总数的高字节
    localparam S_LOADING_INSTR_LSB = 4'b0100; // 等待接收指令的低字节
    localparam S_LOADING_INSTR_MSB = 4'b1000; // 等待接收指令的高字节
    localparam S_LOAD_DONE         = 4'b1001; // 加载完成，等待启动
    localparam S_RUNNING           = 4'b1010; // CPU运行

    // 2. 添加状态寄存器、计数器和临时字节存储器
    reg [3:0] state_reg;
    reg [7:0] temp_lsb_reg; // 用于暂存接收到的低字节
    reg [`WORD_WIDTH-1:0] expected_instr_count_reg;
    reg [`WORD_WIDTH-1:0] received_instr_count_reg;
    
    // 内部信号
    wire [7:0] uart_received_byte; // UART现在输出8位字节
    wire uart_byte_valid;
    wire [`WORD_WIDTH-1:0] MachineCodeData; // 拼接后的16位数据
    // ... 其他信号声明与之前类似

    // 3. 拼接逻辑
    assign MachineCodeData = {uart_received_byte, temp_lsb_reg}; // MSB在高位，LSB在低位

    // 4. 根据状态控制LED和CPU运行
    assign led_cpu_paused = (state_reg != S_LOAD_DONE) && (state_reg != S_RUNNING);
    // ... 其他assign语句与方案二类似

    // 5. 状态机逻辑 (核心改动)
    initial begin
        state_reg <= S_WAIT_COUNT;
        // ... 其他寄存器初始化
    end

    always @(posedge CLK) begin
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
                    // instr_mem_write_enable_internal 会在此状态且uart_byte_valid时为高
                    
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
                if (RESET) begin
                    state_reg <= S_RUNNING;
                end
            end
            
            S_RUNNING: begin
                if (RESET) begin
                    // 保持运行，CPU核心会被复位
                end
            end
            default: state_reg <= S_WAIT_COUNT;
        endcase
    end

    // 6. 指令存储器写使能逻辑
    // 只有在接收到一条指令的高字节时，才产生写使能脉冲
    assign instr_mem_write_enable_internal = (state_reg == S_LOADING_INSTR_MSB) && uart_byte_valid;

    // --- 模块实例化 ---
    // 7. 实例化新的8位UART模块
    uart_rx_byte u_uart_rx (
        .CLK(CLK),
        .rst(RESET),
        .rx_in(uart_rx_pin),
        .data_out(uart_received_byte), // 连接到8位数据线
        .data_valid(uart_byte_valid)
    );

    // 8. instruction_memory的写数据端口连接到拼接后的数据
    instruction_memory u_instr_mem (
        .CLK(CLK),
        .write_addr(MachineCodeAddress),
        .write_data(MachineCodeData), // 写入拼接后的16位指令
        .write_en(instr_mem_write_enable_internal),
        // ... 其他连接不变
    );
    
    // ... 其他模块实例化与方案二相同，确保rst和run_en信号连接正确
    // 例如 cpu_core 的 .rst 连接到 cpu_core_rst_internal
    
endmodule


// **`top_module.v` 代码的重要说明**:

// * 为了代码简洁，我只展示了 `top_module.v` 中与此修改最相关的部分。您需要将这些逻辑整合到您完整的 `top_module.v` 文件中，确保其他信号（如 `cpu_core_rst_internal`, `cpu_run_enable`, `data_mem` 接口等）的定义和连接与方案二保持一致。
// * **核心逻辑**在于状态机现在有 `_LSB` 和 `_MSB` 两种状态，用于区分接收到的是16位数据的前半部分还是后半部分。
// * `temp_lsb_reg` 寄存器是关键，它像一个“中转站”，用于暂存低字节，直到高字节到达后一起进行拼接。

// 完成以上所有修改后，您的项目就能够通过标准的逐字节串口通信，从文件中加载任意长度的程序到您的CPU中，这使得整个系统的设计更加灵活和
