module Instruction_Memory(
    input             clk,       // 时钟信号（用于同步读取）
    input      [31:0] PC,        // 程序计数器输入
    output reg [31:0] inst       // 输出指令
);

// 存储器定义（默认4KB容量，1024个32位单元）
reg [31:0] mem [0:1023]; 

// 初始化指令存储器（使用外部文件加载）
initial begin
    $readmemh("inst_mem.txt", mem);  // 请自行创建指令文件
end

// 同步读取逻辑（Vivado推荐同步读取）
always @(posedge clk) begin
    inst <= mem[PC[11:2]];  // 将字节地址转换为字地址（右移2位）
end

endmodule
