// uart_rx_byte.v
// 标准的8位UART接收器
// 帧格式: 1 start bit, 8 data bits (LSB first), 1 stop bit

module uart_rx_byte (
    input clk,          // 系统时钟
    input rst,          // 复位信号
    input rx_in,        // UART串行输入

    output reg [7:0] data_out, // 接收到的8位数据
    output reg data_valid  // 数据有效信号 (高电平一个时钟周期)
);

    parameter CLKS_PER_BIT = 5208; // 示例: 50MHz clk, 9600 baud (50,000,000 / 9600)
                                   // 请根据您的时钟频率和期望波特率修改此值

    localparam STATE_IDLE = 2'b00;
    localparam STATE_START = 2'b01;
    localparam STATE_DATA = 2'b10;
    localparam STATE_STOP = 2'b11;

    reg [1:0] state_reg;
    reg [15:0] clk_counter_reg; // 波特率时钟计数器
    reg [3:0] bit_counter_reg;  // 已接收数据位数计数器 (0-7 for 8 bits)
    reg [7:0] data_shift_reg;   // 8位数据移位寄存器

    always @(posedge clk or posedge rst) begin
        if (rst) begin
            state_reg <= STATE_IDLE;
            clk_counter_reg <= 0;
            bit_counter_reg <= 0;
            data_shift_reg <= 0;
            data_out <= 0;
            data_valid <= 0;
        end else begin
            data_valid <= 0; // 默认为无效

            case (state_reg)
                STATE_IDLE: begin
                    if (~rx_in) begin // 检测到起始位 (低电平)
                        state_reg <= STATE_START;
                        clk_counter_reg <= 0; 
                    end
                end

                STATE_START: begin
                    if (clk_counter_reg == (CLKS_PER_BIT / 2) - 1) begin // 等待半个bit时间, 在中间采样
                        if (~rx_in) begin // 确认是有效的起始位
                            state_reg <= STATE_DATA;
                            clk_counter_reg <= 0;
                            bit_counter_reg <= 0;
                        end else begin
                            state_reg <= STATE_IDLE;
                        end
                    end else begin
                        clk_counter_reg <= clk_counter_reg + 1;
                    end
                end

                STATE_DATA: begin
                    if (clk_counter_reg == CLKS_PER_BIT - 1) begin // 一个bit时间结束
                        clk_counter_reg <= 0;
                        data_shift_reg <= {rx_in, data_shift_reg[7:1]}; // LSB first
                        
                        if (bit_counter_reg == 7) begin // 接收完8位数据
                            state_reg <= STATE_STOP;
                        end else begin
                            bit_counter_reg <= bit_counter_reg + 1;
                        end
                    end else begin
                        clk_counter_reg <= clk_counter_reg + 1;
                    end
                end

                STATE_STOP: begin
                    if (clk_counter_reg == CLKS_PER_BIT - 1) begin // 一个bit时间结束 (停止位)
                        if (rx_in) begin // 停止位应为高电平
                            data_out <= data_shift_reg;
                            data_valid <= 1; // 数据有效
                        end
                        state_reg <= STATE_IDLE; // 无论停止位是否正确，都返回IDLE
                    end else begin
                        clk_counter_reg <= clk_counter_reg + 1;
                    end
                end
                default: state_reg <= STATE_IDLE;
            endcase
        end
    end
endmodule
