
module InstructionMemory_tb();
// 输入信号
    reg [15:0] IAddress;     // 指令地址
    reg InsMemRW;             // 读写信号

    // 输出信号
    wire [3:0] op;           // 操作码
    wire [3:0] rs;           // 源操作数1
    wire [3:0] rt;           // 源操作数2
    wire [3:0] rd;           // 目的操作数
    wire [15:0] instruction; // 指令

    // 实例化 InstructionMemory 模块

    InstructionMemory uut (
        .IAddress(IAddress),
        .InsMemRW(InsMemRW),
        .op(op),
        .rs(rs),
        .rt(rt),
        .rd(rd),
        .instruction(instruction)
    );

     // 初始块：初始化信号，并进行测试
    initial begin
        // 初始化信号
        InsMemRW = 0;      // 读操作
        IAddress = 0;      // 从地址 0 开始读取指令


        // 读取地址 0 到 3 的指令
        #10 IAddress = 0;  // 读取指令地址 0
        #10 IAddress = 1;  // 读取指令地址 1
        #10 IAddress = 2;  // 读取指令地址 2
        #10 IAddress = 3;  // 读取指令地址 3

        // 结束仿真
        #10 $finish;
    end



endmodule