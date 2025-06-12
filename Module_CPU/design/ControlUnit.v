// 控制器
/*操作码
jal 0000 
jalr 0001
beq 0010
ble 0011
lb  0100
lw  0101
sb  0110
sw  0111
add 1000
sub 1001
and 1010
or  1011
addi 1100
subi 1101
加载高位立即数 lui rd, imm 1110

*/
module ControlUnit(
    input  wire[3:0]  op,   //操作码
    input wire zero, //ALU的zero输出

    // 控制信号
    output reg[1:0]    m2reg, //决定写回寄存器文件来源。 0：把ALU的运算结果传回，1：把数据存储器的数据传回 2:把currentAddress_2传回 3：把立即数左移八位后的数据传回
    output reg[1:0]    PCsrc,    //控制程序计数器（PC）的更新来源，通常用于分支或跳转操作。
    output reg    wmem, //控制存储器的写操作, 0为读，1为写
    output reg memc,    //控制写一字节还是两个字节，memc=0为1字节，memc=1为两个字节。
    output reg[2:0]  ALUOp, //控制 ALU 的操作类型，通常用于选择 ALU 的加法、减法、逻辑运算等操作。0：add, 1：sub, 2：and, 3：or 4:beq 5:ble
    output reg    alucsrc,  // 控制 ALU 的输入来源，通常用于选择 ALU 的操作数。0为寄存器的数（add),1为立即数（addi)
    output reg    wreg  // 控制寄存器的写操作  1为写回，0为不写回
    // output reg    jal   // 控制跳转指令的跳转类型，通常用于选择跳转指令的类型。1为跳转，0为不跳转
);

initial begin
    m2reg = 0;
    PCsrc = 0;
    wmem = 0;
    memc = 0;
    ALUOp = 0;
    alucsrc = 0;
    wreg = 0;
    // jal = 0;
end

always @(*) begin
    case(op)
        4'b0000:begin   //jal
            m2reg = 2;
            PCsrc = 1; //执行 PC = PC + imm
            wmem = 0;
            ALUOp = 3'b000;
            alucsrc = 0;    
            wreg = 1'b1;
            // jal = 1'b1;
        end
        4'b0001:begin   //jalr
            m2reg = 2;
            PCsrc = 2; //执行 PC = rs1 + imm    
            wmem = 0;
            ALUOp = 3'b000;
            alucsrc = 1;    //把立即数传给ALU
            wreg = 1'b1;
            // jal = 1'b1;
        end
        4'b0010:begin   //beq
            PCsrc = 0;
            memc = 0;
            m2reg = 1'b0;    
            wmem = 1'b0;
            ALUOp = 3'b100;
            alucsrc = 0;
            wreg = 1'b0;
            // jal = 1'b0;
            if (!zero) begin    //作为条件
                PCsrc = 2'b01;  //执行 PC = PC + imm
            end
            else begin  //作为正常逻辑语句
                PCsrc = 2'b00;  //执行 PC = PC + 2
            end
        end
        4'b0011:begin   //ble
            m2reg = 1'b0;    
            wmem = 1'b0;
            ALUOp = 3'b101;
            alucsrc = 1'b0;
            wreg = 1'b0;
            // jal = 1'b0;
            if (!zero) begin    //作为条件
                PCsrc = 2'b01;  //执行 PC = PC + imm
            end
            else begin  //作为正常逻辑语句
                PCsrc = 2'b00;  //执行 PC = PC + 2
            end
        end
        4'b0100:begin   //lb
            m2reg = 1'b1;
            PCsrc = 0;
            wmem = 1'b0;
            memc = 0;
            ALUOp = 0;
            alucsrc = 1;
            wreg = 1;
            // jal = 1'b0;
            
        end
        4'b0101:begin   //lw
            m2reg = 1;
            PCsrc = 0;
            wmem = 0;
            memc = 1;
            ALUOp = 0;
            alucsrc = 1;
            wreg = 1;
            // jal = 0;
        end
        4'b0110:begin   //sb

            m2reg = 0;
            PCsrc = 0;
            wmem = 1;
            memc = 0;
            ALUOp = 0;
            alucsrc = 1;
            wreg = 0;
            // jal = 0;
        end
        4'b0111:begin   //sw
            m2reg = 0;
            PCsrc = 0;  
            wmem = 1'b1;
            memc = 1;
            ALUOp = 0;
            alucsrc = 1;
            wreg = 0;
            // jal = 1'b0;
        end
        4'b1000:begin   //add
            m2reg = 0;
            PCsrc = 0;
            wmem = 0;
            memc = 0;
            ALUOp = 3'b000;
            alucsrc = 1'b0;
            wreg = 1'b1;
            // jal = 1'b0;
        end
        4'b1001:begin   //sub
            m2reg = 0;
            PCsrc = 0;
            wmem = 0;
            memc = 0;
            ALUOp = 3'b001;
            alucsrc = 1'b0;
            wreg = 1'b1;
            // jal = 1'b0;

        end
        4'b1010:begin   //and
            m2reg = 0;
            PCsrc = 0;
            wmem = 0;
            memc = 0;
            ALUOp = 3'b010;
            alucsrc = 1'b0;
            wreg = 1'b1;
            // jal = 1'b0;
            
        end
        4'b1011:begin   //or
            m2reg = 0;
            PCsrc = 0;
            wmem = 0;
            memc = 0;
            ALUOp = 3'b011;
            alucsrc = 1'b0;
            wreg = 1'b1;
            // jal = 1'b0;
            
        end
        4'b1100:begin   //addi
            m2reg = 0;
            PCsrc = 0;
            wmem = 0;
            memc = 0;
            ALUOp = 3'b000;
            alucsrc = 1'b1;
            wreg = 1'b1;
            // jal = 1'b0;
            
        end
        4'b1101:begin   //subi
            m2reg = 0;
            PCsrc = 0;
            wmem = 0;
            memc = 0;
            ALUOp = 3'b001;
            alucsrc = 1'b1;
            wreg = 1'b1;
            // jal = 1'b0;
            
        end
        4'b1110:begin   //lui rd,imm 加载高位立即数
            m2reg = 3;
            PCsrc = 0;
            wmem = 0;
            memc = 0;
            ALUOp = 3'b000;
            alucsrc = 0;
            wreg = 1'b1;
            // jal = 1'b0;

        end
        // 4'b1111:begin   //ori

        //     m2reg = 0;
        //     PCsrc = 0;
        //     wmem = 0;
        //     memc = 0;
        //     ALUOp = 3'b011;
        //     alucsrc = 1'b1;
        //     wreg = 1'b1;
        //     jal = 1'b0;
        // end
    endcase
end



endmodule
