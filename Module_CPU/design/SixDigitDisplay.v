module SixDigitDisplay 
(
    input sys_clk,           // 系统时钟（50MHz）
    input sys_rst_n,         // 复位信号（低有效）
    input [7:0] data0,   // 第1位数据（DIG1，0-15）
    input [7:0] data1,   // 第2位数据（DIG2）
    input [7:0] data2,   // 第3位数据（DIG3）
    input [7:0] data3,   // 第4位数据（DIG4）
    input [7:0] data4,   // 第5位数据（DIG5）
    input [7:0] data5,   // 第6位数据（DIG6）
    output reg dig1,    //数码管从左到右为1-6
    output reg dig2,
    output reg dig3,
    output reg dig4, 
    output reg dig5, 
    output reg dig6, 
    output reg[6:0] out 
);

reg[2:0] digit_select; // 用于选择当前显示的数码管
reg[15:0] dig_counter; // 用于计数 50000 个时钟周期

initial begin
    dig1 <= 1'b0;
    dig2 <= 1'b0;
    dig3 <= 1'b0;
    dig4 <= 1'b0;
    dig5 <= 1'b0;
    dig6 <= 1'b0;
    digit_select <= 3'b0;
    dig_counter <= 0;
end

always @(posedge sys_clk or negedge sys_rst_n) begin
        if(!sys_rst_n) begin
            digit_select <= 2'b00;
            dig_counter <= 0;
        end
        else begin
            if (dig_counter < 50000) begin      //数码管的更新周期为50000ns
                dig_counter = dig_counter + 1;
            end
            else begin      //完成一个周期后，进行下一个数码管的更新
                dig_counter <= 0;
                if (digit_select == 3'b101) begin
                    digit_select <= 3'b000;
                end
                else begin
                    digit_select <= digit_select + 1;
                end
            end 
        end
    end



always@(posedge sys_clk) begin
        case(digit_select)
            3'b000: begin
                dig1 = 1'b1; dig2 = 1'b0; dig3 = 1'b0; dig4 = 1'b0; dig5 = 1'b0; dig6 = 1'b0;
                case(data5[3:0])
                    4'b0000: out = 7'b1000000; // 0
                    4'b0001: out = 7'b1111001; // 1
                    4'b0010: out = 7'b0100100; // 2
                    4'b0011: out = 7'b0110000; // 3
                    4'b0100: out = 7'b0011001; // 4
                    4'b0101: out = 7'b0010010; // 5
                    4'b0110: out = 7'b0000010; // 6
                    4'b0111: out = 7'b1111000; // 7
                    4'b1000: out = 7'b0000000; // 8
                    4'b1001: out = 7'b0010000; // 9
                    4'b1010: out = 7'b0001000; // A
                    4'b1011: out = 7'b0000011; // b
                    4'b1100: out = 7'b1000110; // C
                    4'b1101: out = 7'b0100001; // d
                    4'b1110: out = 7'b0000110; // E
                    4'b1111: out = 7'b0001110; // F
                endcase
            end

            3'b001: begin
                dig1 = 1'b0; dig2 = 1'b1; dig3 = 1'b0; dig4 = 1'b0; dig5 = 1'b0; dig6 = 1'b0;
                case(data4[3:0])
                    4'b0000: out = 7'b1000000; // 0
                    4'b0001: out = 7'b1111001; // 1
                    4'b0010: out = 7'b0100100; // 2
                    4'b0011: out = 7'b0110000; // 3
                    4'b0100: out = 7'b0011001; // 4
                    4'b0101: out = 7'b0010010; // 5
                    4'b0110: out = 7'b0000010; // 6
                    4'b0111: out = 7'b1111000; // 7
                    4'b1000: out = 7'b0000000; // 8
                    4'b1001: out = 7'b0010000; // 9
                    4'b1010: out = 7'b0001000; // A
                    4'b1011: out = 7'b0000011; // b
                    4'b1100: out = 7'b1000110; // C
                    4'b1101: out = 7'b0100001; // d
                    4'b1110: out = 7'b0000110; // E
                    4'b1111: out = 7'b0001110; // F
                endcase
            end

            3'b010: begin
                dig1 = 1'b0; dig2 = 1'b0; dig3 = 1'b1; dig4 = 1'b0; dig5 = 1'b0; dig6 = 1'b0;
                case(data3[3:0])
                    4'b0000: out = 7'b1000000; // 0
                    4'b0001: out = 7'b1111001; // 1
                    4'b0010: out = 7'b0100100; // 2
                    4'b0011: out = 7'b0110000; // 3
                    4'b0100: out = 7'b0011001; // 4
                    4'b0101: out = 7'b0010010; // 5
                    4'b0110: out = 7'b0000010; // 6
                    4'b0111: out = 7'b1111000; // 7
                    4'b1000: out = 7'b0000000; // 8
                    4'b1001: out = 7'b0010000; // 9
                    4'b1010: out = 7'b0001000; // A
                    4'b1011: out = 7'b0000011; // b
                    4'b1100: out = 7'b1000110; // C
                    4'b1101: out = 7'b0100001; // d
                    4'b1110: out = 7'b0000110; // E
                    4'b1111: out = 7'b0001110; // F
                endcase
            end

            3'b011: begin
                dig1 = 1'b0; dig2 = 1'b0; dig3 = 1'b0; dig4 = 1'b1; dig5 = 1'b0; dig6 = 1'b0;
                case(data2[3:0])
                    4'b0000: out = 7'b1000000; // 0
                    4'b0001: out = 7'b1111001; // 1
                    4'b0010: out = 7'b0100100; // 2
                    4'b0011: out = 7'b0110000; // 3
                    4'b0100: out = 7'b0011001; // 4
                    4'b0101: out = 7'b0010010; // 5
                    4'b0110: out = 7'b0000010; // 6
                    4'b0111: out = 7'b1111000; // 7
                    4'b1000: out = 7'b0000000; // 8
                    4'b1001: out = 7'b0010000; // 9
                    4'b1010: out = 7'b0001000; // A
                    4'b1011: out = 7'b0000011; // b
                    4'b1100: out = 7'b1000110; // C
                    4'b1101: out = 7'b0100001; // d
                    4'b1110: out = 7'b0000110; // E
                    4'b1111: out = 7'b0001110; // F
                endcase
            end
            3'b100: begin
                dig1 = 1'b0; dig2 = 1'b0; dig3 = 1'b0; dig4 = 1'b0; dig5 = 1'b1; dig6 = 1'b0;
                case(data1[3:0])
                    4'b0000: out = 7'b1000000; // 0
                    4'b0001: out = 7'b1111001; // 1
                    4'b0010: out = 7'b0100100; // 2
                    4'b0011: out = 7'b0110000; // 3
                    4'b0100: out = 7'b0011001; // 4
                    4'b0101: out = 7'b0010010; // 5
                    4'b0110: out = 7'b0000010; // 6
                    4'b0111: out = 7'b1111000; // 7
                    4'b1000: out = 7'b0000000; // 8
                    4'b1001: out = 7'b0010000; // 9
                    4'b1010: out = 7'b0001000; // A
                    4'b1011: out = 7'b0000011; // b
                    4'b1100: out = 7'b1000110; // C
                    4'b1101: out = 7'b0100001; // d
                    4'b1110: out = 7'b0000110; // E
                    4'b1111: out = 7'b0001110; // F
                endcase
            end
            3'b101: begin
                dig1 = 1'b0; dig2 = 1'b0; dig3 = 1'b0; dig4 = 1'b0; dig5 = 1'b0; dig6 = 1'b1;
                case(data0[3:0])
                    4'b0000: out = 7'b1000000; // 0
                    4'b0001: out = 7'b1111001; // 1
                    4'b0010: out = 7'b0100100; // 2
                    4'b0011: out = 7'b0110000; // 3
                    4'b0100: out = 7'b0011001; // 4
                    4'b0101: out = 7'b0010010; // 5
                    4'b0110: out = 7'b0000010; // 6
                    4'b0111: out = 7'b1111000; // 7
                    4'b1000: out = 7'b0000000; // 8
                    4'b1001: out = 7'b0010000; // 9
                    4'b1010: out = 7'b0001000; // A
                    4'b1011: out = 7'b0000011; // b
                    4'b1100: out = 7'b1000110; // C
                    4'b1101: out = 7'b0100001; // d
                    4'b1110: out = 7'b0000110; // E
                    4'b1111: out = 7'b0001110; // F
                endcase
            end
        endcase
    end


endmodule