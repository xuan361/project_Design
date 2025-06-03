
// InstructionMemory：储存指令，分割指令
// 指令地址是以字节为单位的，而内存地址是以字为单位的。
// 所以，指令地址需要右移一位才能得到对应的内存地址。
module InstructionMemory(
    input CLK,
    input instr_mem_write_enable,     //读写信号，1为写，0为读

    input [15:0] MachineCodeAddress,    //机器码对应的地址
    input [15:0] MachineCodeData,   //机器码数据
    input [15:0] ROMDataAddress,    //ROM数据地址

    input [15:0] IAddress,   //指令地址输入入口

    output reg[3:0] op,    //操作码
    output reg[3:0] rs,    //源操作数1
    output reg[3:0] rt,    //源操作数2
    output reg[3:0] rd,    //目的操作数
    output reg[15:0] instruction, //传递给立即数扩展模块的指令

    output reg[15:0] DataFromROM
);

    reg[15:0] ROM[0:255]; //ROM 用于存储指令数据，总共有 256 个 16 位的元素。也就是512个字节。
    integer i;

    // initial 
    // begin
    //     $readmemb("D:/learn/Git/testgit/test/test2.txt", ROM);  //读取测试文档中的指令
    // end
    initial begin
        for(i = 0; i < 256; i = i + 1) begin
            ROM[i] = 16'b0;
        end
    end


    always @(posedge CLK)begin
        if(instr_mem_write_enable) begin
            ROM[MachineCodeAddress] = MachineCodeData;
        end
    end

    always @(*)begin
        op = ROM[IAddress >> 1][3:0];
        rd = ROM[IAddress >> 1][7:4];
        rs = ROM[IAddress >> 1][11:8];
        rt = ROM[IAddress >> 1][15:12];
        instruction = ROM[IAddress >> 1];

        if(ROMDataAddress[0] == 0)
            DataFromROM = {8'b0, ROM[ROMDataAddress >> 1][15:8]};
        else
            DataFromROM = {8'b0, ROM[ROMDataAddress >> 1][7:0]};
    end



endmodule





