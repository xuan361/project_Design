// register_file.v
`include "defines.vh"

module register_file (
    input clk,
    input rst,
    input write_en,         // 写使能
    input [`REG_ADDR_WIDTH-1:0] read_addr1, // 读地址1
    input [`REG_ADDR_WIDTH-1:0] read_addr2, // 读地址2
    input [`REG_ADDR_WIDTH-1:0] write_addr, // 写地址
    input [`WORD_WIDTH-1:0] write_data,   // 写入数据
    output [`WORD_WIDTH-1:0] read_data1,  // 读数据1
    output [`WORD_WIDTH-1:0] read_data2   // 读数据2
);

    // 16个16位寄存器
    reg [`WORD_WIDTH-1:0] registers [`NUM_REGS-1:0];
    integer i;

    // 写操作 (同步写)
    always @(posedge clk) begin
        if (write_en) begin
            if (write_addr != 0) begin // R0 通常为硬编码0，或者根据设计允许写入
                registers[write_addr] <= write_data;
            end
        end
    end
    
    // 如果需要R0硬编码为0，则在初始化时设置
    always @(posedge clk or posedge rst) begin
        if (rst) begin
            for (i = 0; i < `NUM_REGS; i = i + 1) begin
                registers[i] <= 0;
            end
        end
    end


    // 读操作 (异步读)
    // R0总是返回0
    assign read_data1 = (read_addr1 == 0) ? `WORD_WIDTH'b0 : registers[read_addr1];
    assign read_data2 = (read_addr2 == 0) ? `WORD_WIDTH'b0 : registers[read_addr2];

endmodule
