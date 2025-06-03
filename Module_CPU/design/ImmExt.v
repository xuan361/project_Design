
// ImmExt: 用于immediate的扩展

module ImmExt(
    input [15:0] instruction,   //指令
    output reg[15:0] immExt    //扩展后的立即数
);  
    reg[3:0] op;
    reg[3:0] imm_4;
    reg[7:0] imm_8;

// 取指令中的立即数
always @(*)begin
    op = instruction[3:0];
    case(op)    
        4'b0000:begin   //jal
            imm_8 = (instruction[15:8]);
            // immExt[15:8] = imm_8[7] ? 8'b1111_1111 : 0;
            // immExt[7:0] = imm_8;
            immExt = {{7{imm_8[7]}}, imm_8, 1'b0};
        end
        4'b0001:begin   //jalr
            imm_4 = instruction[15:12];
            // immExt[15:4] = imm_4[3] ? 12'b1111_1111_1111 : 0;
            // immExt[3:0] = imm_4;
            immExt = {{11{imm_4[3]}}, imm_4, 1'b0};                        
        end
        4'b0010, 4'b0011:begin  //beq, ble
            imm_4 = instruction[7:4];
            // immExt[15:4] = imm_4[3] ? 12'b1111_1111_1111 : 0;
            // immExt[3:0] = imm_4; 
            immExt = {{11{imm_4[3]}}, imm_4, 1'b0};   
        end

        4'b0100, 4'b0101:begin  //lb, lw
            imm_4 = instruction[15:12];
            immExt[15:4] = imm_4[3] ? 12'b1111_1111_1111 : 0;
            immExt[3:0] = imm_4; 
        end

        4'b0110, 4'b0111:begin  //sb, sw
            imm_4 = instruction[7:4];
            immExt[15:4] = imm_4[3] ? 12'b1111_1111_1111 : 0;
            immExt[3:0] = imm_4; 
        end

        // 4'b1100, 4'b1101, 4'b1110, 4'b1111:begin  //addi, subi, andi, ori
        //     imm_4 = instruction[15:12];
        //     immExt[15:4] = imm_4[3] ? 12'b1111_1111_1111 : 0;
        //     immExt[3:0] = imm_4; 

        4'b1100, 4'b1101:begin  //addi, subi
            imm_4 = instruction[15:12];
            immExt[15:4] = imm_4[3] ? 12'b1111_1111_1111 : 0;
            immExt[3:0] = imm_4; 
        end

        4'b1110: begin  // lui
            imm_8 = instruction[15:8];
            immExt = {imm_8, 8'b0};
        end

    endcase
end


endmodule
