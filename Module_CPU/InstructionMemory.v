
// InstructionMemory：储存指令，分割指令
module InstructionMemory(
    input InsMemRW,     //读写信号，1为写，0为读
    input [15:0] IAddress,   //指令地址输入入口
    // input [15:0] IData,   //指令数据

    output [3:0] op,    //操作码
    output [3:0] rs,    //源操作数
    output [3:0] rt,    //目的操作数
    output [3:0] rd,    
    output [3:0] imm    //立即数
);
    reg[15:0] mem[0:31]; //mem 用于存储指令数据，总共有 32 个 16 位的元素。

    initial 
     begin
        $readmemb("test/test.txt", mem);  //读取测试文档中的指令
     end

    // 从地址取值然后输出
    assign op = mem[IAddress][3:0];
    assign rs = mem[IAddress][7:4];
    assign rt = mem[IAddress][11:8];
    // assign rd = mem[IAddress][15:12];
    assign imm = mem[IAddress][15:12];



endmodule





