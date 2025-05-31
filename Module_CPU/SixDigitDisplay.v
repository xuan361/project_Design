//六位数码管显示屏
//输入六个数字， 返回 段选信号 和 位选信号
module SixDigitDisplay(
    input clk,           // 系统时钟（50MHz）
    input rst_n,         // 复位信号（低有效）
    input [7:0] data0,   // 第1位数据（DIG1，0-15）
    input [7:0] data1,   // 第2位数据（DIG2）
    input [7:0] data2,   // 第3位数据（DIG3）
    input [7:0] data3,   // 第4位数据（DIG4）
    input [7:0] data4,   // 第5位数据（DIG5）
    input [7:0] data5,   // 第6位数据（DIG6）
    output reg [6:0] seg,// 段选信号（共阳，a-g=seg[6:0]）
    output reg [5:0] sel // 位选信号（低有效，DIG1-DIG6）
);

parameter CLK_DIV = 16'd49999; // 50MHz→1kHz分频系数

reg [15:0] clk_cnt;      // 时钟分频计数器
reg [2:0] scan_cnt;      // 扫描计数器（0-5，对应DIG1-DIG6）
reg [7:0] data_reg;      // 当前显示数据
reg [7:0] data_store [5:0]; // 数据锁存寄存器（0-5对应DIG1-DIG6）


// 时钟分频（50MHz→1kHz）
always @(posedge clk or negedge rst_n) begin
    if(!rst_n) 
        clk_cnt <= 16'd0;
    else 
        clk_cnt <= (clk_cnt == CLK_DIV) ? 16'd0 : clk_cnt + 1'b1;
end

// 数据锁存（防抖动）
always @(posedge clk) begin
    if(clk_cnt == CLK_DIV) begin  
        data_store[0] <= data0;  // DIG1
        data_store[1] <= data1;  // DIG2
        data_store[2] <= data2;  // DIG3
        data_store[3] <= data3;  // DIG4
        data_store[4] <= data4;  // DIG5
        data_store[5] <= data5;  // DIG6
    end
end

// 扫描计数器（0-5循环）
always @(posedge clk or negedge rst_n) begin
    if(!rst_n) 
        scan_cnt <= 3'd0;
    else if(clk_cnt == CLK_DIV)  
        scan_cnt <= (scan_cnt == 3'd5) ? 3'd0 : scan_cnt + 1'b1;
end


always @(*) begin
    case(scan_cnt)  // 扫描6个数码管位
        //DIG1（data0）
        3'd0: begin  
            sel = 6'b111110; 
            case(data_store[0])
                4'h0: seg = 7'b1000000; // 0
                4'h1: seg = 7'b1111001; // 1
                4'h2: seg = 7'b0100100; // 2
                4'h3: seg = 7'b0110000; // 3
                4'h4: seg = 7'b0011001; // 4
                4'h5: seg = 7'b0010010; // 5
                4'h6: seg = 7'b0000010; // 6
                4'h7: seg = 7'b1111000; // 7
                4'h8: seg = 7'b0000000; // 8
                4'h9: seg = 7'b0010000; // 9
                4'ha: seg = 7'b0001000; // A
                4'hb: seg = 7'b0000011; // b
                4'hc: seg = 7'b1000110; // C
                4'hd: seg = 7'b0100001; // d
                4'he: seg = 7'b0000110; // E
                4'hf: seg = 7'b0001110; // F
                default: seg = 7'b1111111; // 全灭
            endcase
        end

        //DIG2（data1）
        3'd1: begin  
            sel = 6'b111101; 
            case(data_store[1])  
                4'h0: seg = 7'b1000000; // 0
                4'h1: seg = 7'b1111001; // 1
                4'h2: seg = 7'b0100100; // 2
                4'h3: seg = 7'b0110000; // 3
                4'h4: seg = 7'b0011001; // 4
                4'h5: seg = 7'b0010010; // 5
                4'h6: seg = 7'b0000010; // 6
                4'h7: seg = 7'b1111000; // 7
                4'h8: seg = 7'b0000000; // 8
                4'h9: seg = 7'b0010000; // 9
                4'ha: seg = 7'b0001000; // A
                4'hb: seg = 7'b0000011; // b
                4'hc: seg = 7'b1000110; // C
                4'hd: seg = 7'b0100001; // d
                4'he: seg = 7'b0000110; // E
                4'hf: seg = 7'b0001110; // F
                default: seg = 7'b1111111; 
            endcase
        end

        //DIG3（data2）
        3'd2: begin  
            sel = 6'b111011; 
            case(data_store[2])  
                4'h0: seg = 7'b1000000; // 0
                4'h1: seg = 7'b1111001; // 1 
                4'h2: seg = 7'b0100100; // 2
                4'h3: seg = 7'b0110000; // 3
                4'h4: seg = 7'b0011001; // 4
                4'h5: seg = 7'b0010010; // 5
                4'h6: seg = 7'b0000010; // 6
                4'h7: seg = 7'b1111000; // 7
                4'h8: seg = 7'b0000000; // 8
                4'h9: seg = 7'b0010000; // 9
                4'ha: seg = 7'b0001000; // A
                4'hb: seg = 7'b0000011; // b
                4'hc: seg = 7'b1000110; // C
                4'hd: seg = 7'b0100001; // d
                4'he: seg = 7'b0000110; // E
                4'hf: seg = 7'b0001110; // F
                default: seg = 7'b1111111; 
            endcase
        end

        //DIG4（data3）
        3'd3: begin  
            sel = 6'b110111; 
            case(data_store[3])  
                4'h0: seg = 7'b1000000; // 0
                4'h1: seg = 7'b1111001; // 1 
                4'h2: seg = 7'b0100100; // 2
                4'h3: seg = 7'b0110000; // 3
                4'h4: seg = 7'b0011001; // 4
                4'h5: seg = 7'b0010010; // 5
                4'h6: seg = 7'b0000010; // 6
                4'h7: seg = 7'b1111000; // 7
                4'h8: seg = 7'b0000000; // 8
                4'h9: seg = 7'b0010000; // 9
                4'ha: seg = 7'b0001000; // A
                4'hb: seg = 7'b0000011; // b
                4'hc: seg = 7'b1000110; // C
                4'hd: seg = 7'b0100001; // d
                4'he: seg = 7'b0000110; // E
                4'hf: seg = 7'b0001110; // F
                default: seg = 7'b1111111; 
            endcase
        end

        //DIG5（data4）
        3'd4: begin  
            sel = 6'b101111; 
            case(data_store[4])  
                4'h0: seg = 7'b1000000; // 0
                4'h1: seg = 7'b1111001; // 1 
                4'h2: seg = 7'b0100100; // 2
                4'h3: seg = 7'b0110000; // 3
                4'h4: seg = 7'b0011001; // 4
                4'h5: seg = 7'b0010010; // 5
                4'h6: seg = 7'b0000010; // 6
                4'h7: seg = 7'b1111000; // 7
                4'h8: seg = 7'b0000000; // 8
                4'h9: seg = 7'b0010000; // 9
                4'ha: seg = 7'b0001000; // A
                4'hb: seg = 7'b0000011; // b
                4'hc: seg = 7'b1000110; // C
                4'hd: seg = 7'b0100001; // d
                4'he: seg = 7'b0000110; // E
                4'hf: seg = 7'b0001110; // F 
                default: seg = 7'b1111111; 
            endcase
        end

        //DIG6（data5）
        3'd5: begin  
            sel = 6'b011111; 
            case(data_store[5])  
                4'h0: seg = 7'b1000000; // 0
                4'h1: seg = 7'b1111001; // 1
                4'h2: seg = 7'b0100100; // 2
                4'h3: seg = 7'b0110000; // 3
                4'h4: seg = 7'b0011001; // 4
                4'h5: seg = 7'b0010010; // 5
                4'h6: seg = 7'b0000010; // 6
                4'h7: seg = 7'b1111000; // 7
                4'h8: seg = 7'b0000000; // 8
                4'h9: seg = 7'b0010000; // 9
                4'ha: seg = 7'b0001000; // A
                4'hb: seg = 7'b0000011; // b
                4'hc: seg = 7'b1000110; // C
                4'hd: seg = 7'b0100001; // d
                4'he: seg = 7'b0000110; // E
                4'hf: seg = 7'b0001110; // F
                default: seg = 7'b1111111; 
            endcase
        end

        default: begin  // 异常
            sel = 6'b111111;
            seg = 7'b1111111;
        end
    endcase
end

endmodule