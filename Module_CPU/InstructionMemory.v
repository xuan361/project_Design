
// InstructionMemory：储存指令，分割指令
module InstructionMemory(
    input InsMemRW,     //读写信号，1为写，0为读
    input [15:0] IAddress,   //指令地址输入入口
    // input [15:0] IData,   //指令数据

    output reg[3:0] op,    //操作码
    output reg[3:0] rs,    //源操作数1
    output reg[3:0] rt,    //源操作数2
    output reg[3:0] rd,    //目的操作数
    output reg[15:0] instruction //传递给立即数扩展模块的指令
);
    reg[15:0] mem[0:63]; //mem 用于存储指令数据，总共有 64 个 16 位的元素。

    initial 
     begin
        $readmemb("test/test.txt", mem);  //读取测试文档中的指令
     end


    always @(*)begin
        op = mem[IAddress][3:0];
        rd = mem[IAddress][7:4];
        rs = mem[IAddress][11:8];
        rt = mem[IAddress][15:12];
        instruction = mem[IAddress];
    end





endmodule





