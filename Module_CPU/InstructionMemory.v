
// InstructionMemory：储存指令，分割指令
module InstructionMemory(
    input InsMemRW,     //读写信号，1为写，0为读
    input [15:0] IAddress,   //指令地址输入入口
    // input [15:0] IData,   //指令数据

    output reg[3:0] op,    //操作码
    output reg[3:0] rs,    //源操作数1
    output reg[3:0] rt,    //源操作数2
    output reg[3:0] rd,    //目的操作数
    output reg[3:0] imm    //立即数
);
    reg[7:0] mem[0:63]; //mem 用于存储指令数据，总共有 64 个 8 位的元素。

    initial 
     begin
        $readmemb("test/test.txt", mem);  //读取测试文档中的指令
     end


    always @(*)begin
        // 从地址取值然后输出
        op = mem[IAddress + 1][3:0];
        case (op)
            4'b0000:begin   //jal
                rd = mem[IAddress + 1][7:4];
                imm = mem[IAddress][3:0];
// 0000 0010 0001 0000
            end
            4'b0001:begin   //jalr
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4];
            end
            4'b0010:begin   //beq
                imm = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                rt = mem[IAddress][7:4];
            end
            4'b0011:begin   //ble
                imm = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                rt = mem[IAddress][7:4];
            end
            4'b0100:begin   //lb
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4];
            end
            4'b0101:begin   //lw
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4];    
            end
            4'b0110:begin   //sb
                 rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4];                    
            end
            4'b0111:begin   //sw
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4]; 
            end
            4'b1000:begin   //add
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                rt = mem[IAddress][7:4]; 
            end
            4'b1001:begin   //sub
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                rt = mem[IAddress][7:4]; 

            end
            4'b1010:begin   //and
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                rt = mem[IAddress][7:4]; 
                
            end
            4'b1011:begin   //or
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                rt = mem[IAddress][7:4]; 
                
            end
            4'b1100:begin   //addi
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4]; 
                
            end
            4'b1101:begin   //subi
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4];    
                
            end
            4'b1110:begin   //andi
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4]; 
            end
            4'b1111:begin   //ori
                rd = mem[IAddress + 1][7:4];
                rs = mem[IAddress][3:0];
                imm = mem[IAddress][7:4]; 
                
            end

        endcase
    end




endmodule





