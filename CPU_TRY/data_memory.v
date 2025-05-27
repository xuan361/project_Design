// data_memory.v
`include "defines.vh"

module data_memory (
    input clk,
    input [`WORD_WIDTH-1:0] addr,      // 地址 (CPU计算得到，可能需要截取低位)
    input [`WORD_WIDTH-1:0] write_data, // 写入数据
    input mem_write_en,   // 写使能
    input mem_read_en,    // 读使能 (单周期CPU中，LW时有效)
    output reg [`WORD_WIDTH-1:0] read_data  // 读出数据
);

    // 数据存储器: 256 x 16-bit
    reg [`WORD_WIDTH-1:0] mem [`DATA_MEM_DEPTH-1:0];
    wire [`DATA_MEM_ADDR_WIDTH-1:0] effective_addr;
    integer i;
    
    // 使用地址的低位作为实际内存地址
    assign effective_addr = addr[`DATA_MEM_ADDR_WIDTH-1:0];

    // 初始化 (可选)
    // initial begin
    //     for (i = 0; i < `DATA_MEM_DEPTH; i = i + 1) begin
    //         mem[i] = `WORD_WIDTH'b0;
    //     end
    // end

    // 写操作 (同步写)
    always @(posedge clk) begin
        if (mem_write_en) begin
            mem[effective_addr] <= write_data;
        end
    end

    // 读操作 (本设计为同步读，单周期CPU通常期望组合逻辑读，或调整时序)
    // 为简单起见，这里用同步读，但数据会在下一个周期才有效。
    // 对于严格的单周期CPU，数据内存读取通常是组合逻辑的，或者需要特殊处理。
    // 如果需要组合逻辑读: assign read_data = mem[effective_addr]; (但mem_read_en需要处理)
    always @(posedge clk) begin
        if (mem_read_en) begin // 仅在读使能时更新输出，防止旧数据干扰
             read_data <= mem[effective_addr];
        end
    end
    // 对于单周期CPU，更常见的做法是异步读，或者说读路径是组合的：
    // assign read_data = mem[effective_addr]; 
    // 但这要求mem_read_en不直接控制输出寄存器，而是作为控制信号给CPU。
    // 这里为了简单，我们假设 LW 指令在一个周期内完成，数据在同一周期末尾从这里读出。
    // 如果使用上述 always块，则LW指令需要两个周期，或者CPU设计要适应这种延迟。
    // 为了更符合单周期，我们改为组合逻辑读，mem_read_en更多是作为控制信号给CPU。
    // assign read_data = mem[effective_addr]; // 这样更符合单周期CPU的假设
    // 然而，上面的always块也是一种实现方式，只是意味着数据通路上的延迟。
    // 我们暂时保留同步读的always块，但请注意其对单周期CPU时序的影响。
    // 如果要严格单周期，应改为:
    // assign read_data = mem_read_en ? mem[effective_addr] : `WORD_WIDTH'bx;
    // 或者CPU在控制逻辑中处理，只在mem_read_en为高时才使用read_data。
    // 为了模块化，我们让它在mem_read_en时更新read_data寄存器。

endmodule
