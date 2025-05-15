`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/12/08 02:17:16
// Design Name: 
// Module Name: division
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////


module division(sys_clk, sys_rst_n, start, dividend, divisor, done, led1, led2, led3, led4, out,shang, yushu);
    parameter WIDTH = 16;

    input wire sys_clk;
    input wire sys_rst_n; // 重置信号，初始化寄存器
    input wire start; // 开始信号

    input wire [15:0] dividend;  //被除数
    input wire [15:0] divisor;   //除数
    output reg [15:0] shang;
    output reg [15:0] yushu;
    
    output reg done;    //高电平表示已完成
    output reg led1;
    output reg led2;
    output reg led3;
    output reg led4;
    output reg[6:0] out;

    reg[5:0] count; // 计数器，用于控制移位次数（最多16次）
    reg[1:0] state; // 0 表示空闲；1 表示运行中；2 表示已完成
    reg[1:0] digit_select; // 用于选择当前显示的数码管
    reg[15:0] counter; // 用于计数 50000 个时钟周期

    // initial begin
    //     state = 1'b0;
    //     done = 1'b0;
    //     led1 = 1'b0;
    //     led2 = 1'b0;
    //     led3 = 1'b0;
    //     led4 = 1'b0;
    //     digit_select = 2'b00;
    //     counter = 0;
    //     yushu <= 0;
    //     shang <= 0;
    // end

    always@(posedge sys_clk or negedge sys_rst_n) begin
        if (sys_rst_n == 0) begin
            state <= 0;
            done <= 0;
            yushu <= 0;
            shang <= 0;
            digit_select <= 2'b00;
            counter <= 0;
        end
        else begin
            if (counter < 50000) begin      //灯的更新周期为50000ns
                counter = counter + 1;
            end
            else begin      //完成一个周期后，进行下一个灯的更新
                counter <= 0;
                if (digit_select == 2'b11) begin
                    digit_select <= 2'b00;
                end
                else begin
                    digit_select <= digit_select + 1;
                end
            end 

            case (state)    // counter小于50000时进行
                0: begin    // 空闲
                    done <= 0;
                    count <= 16;
                    if (start == 0) begin
                        state <= 1;
                    end
                end

                1: begin    //运行中
                    if (count != 0) begin
                        yushu = {yushu[14:0], dividend[count - 1]};  // 左移被除数
                        if(yushu >= divisor) begin
                            yushu = yushu - divisor;
                            shang[count - 1] = 1;    //设置商的相应位
                        end
                        count = count - 1;
                    end
                    else begin
                        state = 2;
                    end
                end

                2: begin    //已完成
                    done <= 1;
                    state <= 0;
                end
            endcase
        end
    end

    always@(posedge sys_clk) begin
        case(digit_select)
            2'b00: begin
                // 数码管的显示从左向右为1-4
                led1 = 1'b1; led2 = 1'b0; led3 = 1'b0; led4 = 1'b0;
                case(shang[15:12])
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

            2'b01: begin
                led1 = 1'b0; led2 = 1'b1; led3 = 1'b0; led4 = 1'b0;
                case(shang[11:8])
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

            2'b10: begin
                led1 = 1'b0; led2 = 1'b0; led3 = 1'b1; led4 = 1'b0;
                case(shang[7:4])
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

            2'b11: begin
                led1 = 1'b0; led2 = 1'b0; led3 = 1'b0; led4 = 1'b1;
                case(shang[3:0])
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
