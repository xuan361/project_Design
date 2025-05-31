// 模块1: 将4位十六进制数转换为7段共阳极码
// seg[6]=a, seg[5]=b, seg[4]=c, seg[3]=d, seg[2]=e, seg[1]=f, seg[0]=g
// 共阳极: 0 = ON, 1 = OFF
module hex_to_7seg (
    input [3:0] hex_digit,       // 输入的4位十六进制数 (0-F)
    output reg [6:0] seg_pattern // 输出的7段码 (abcdefg)
);
    always @(*) begin
        case (hex_digit)
            4'h0: seg_pattern = 7'b0000001; // 0
            4'h1: seg_pattern = 7'b1001111; // 1
            4'h2: seg_pattern = 7'b0010010; // 2
            4'h3: seg_pattern = 7'b0000110; // 3
            4'h4: seg_pattern = 7'b1001100; // 4
            4'h5: seg_pattern = 7'b0100100; // 5
            4'h6: seg_pattern = 7'b0100000; // 6
            4'h7: seg_pattern = 7'b0001111; // 7
            4'h8: seg_pattern = 7'b0000000; // 8
            4'h9: seg_pattern = 7'b0000100; // 9
            4'hA: seg_pattern = 7'b0001000; // A
            4'hB: seg_pattern = 7'b1100000; // b (小写b)
            4'hC: seg_pattern = 7'b0110001; // C (大写C)
            4'hD: seg_pattern = 7'b1000010; // d (小写d)
            4'hE: seg_pattern = 7'b0110000; // E (大写E)
            4'hF: seg_pattern = 7'b0111000; // F (大写F)
            default: seg_pattern = 7'b1111111; // 全灭或错误显示
        endcase
    end
endmodule

//seg 信号决定一个数码管上显示什么图案（哪些段亮）。
// sel 信号决定多个数码管中哪一个当前被激活显示这个图案。

// 模块2: 6位七段数码管扫描显示驱动
module six_digit_7seg_display (
    input clk,         // 系统时钟（50MHz）
    input rst_n,       // 复位信号（低有效）
    input [7:0] data0, // 第1位数据（DIG1，0-15）
    input [7:0] data1, // 第2位数据（DIG2）
    input [7:0] data2, // 第3位数据（DIG3）
    input [7:0] data3, // 第4位数据（DIG4）
    input [7:0] data4, // 第5位数据（DIG5）
    input [7:0] data5, // 第6位数据（DIG6）

    output reg [6:0] seg, // 段选信号（共阳，a-g=seg[6:0]）
    output reg [5:0] sel  // 位选信号（低有效，DIG1-DIG6, sel[0] for DIG1, sel[5] for DIG6）
);

    // 内部信号
    reg [15:0] scan_counter;  // 用于定时切换数码管 (计数 0 到 65535)
    reg [2:0] digit_select;    // 选择当前活动的数码管 (0-5)
    reg reset_display_active;  // 标志位，为1时强制显示0

    wire [3:0] data_for_current_digit;   // 当前选中数码管对应的4位数据
    wire [6:0] seg_pattern_from_decoder; // 从hex_to_7seg解码器输出的段码

    // 在 initial 块中设置内部状态寄存器的初始值
    initial begin
        scan_counter = 16'd0;
        digit_select = 3'd0;         // 初始选择第一个数码管
        reset_display_active = 1'b1; // 激活初始显示0的状态
    end

    // 扫描计数器、数码管选择逻辑 和 reset_display_active 控制逻辑
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin // 低电平有效复位
            scan_counter <= 16'd0;
            digit_select <= 3'd0;
            reset_display_active <= 1'b1; // 复位时，也激活强制显示0的状态
        end else begin
            if (scan_counter == 16'd65535) begin // 一个数码管的显示周期结束
                scan_counter <= 16'd0;
                if (digit_select == 3'd5) begin // 如果当前是最后一个数码管 (DIG6)
                    digit_select <= 3'd0;       // 下一个从第一个数码管 (DIG1) 开始
                    if (reset_display_active) begin // 如果仍在初始显示0的阶段
                        reset_display_active <= 1'b0; // 完成了一个完整扫描周期的强制0显示，取消该状态
                    end
                end else begin
                    digit_select <= digit_select + 1; // 选择下一个数码管
                end
            end else begin
                scan_counter <= scan_counter + 1; // 扫描计数器递增
            end
        end
    end

    // 数据选择器：根据 digit_select 和 reset_display_active 选择当前要显示的4位数据
    assign data_for_current_digit = 
           (reset_display_active) ? 4'b0000 : // 如果 reset_display_active 为1, 强制数据为0
           (digit_select == 3'd0) ? data0[3:0] :
           (digit_select == 3'd1) ? data1[3:0] :
           (digit_select == 3'd2) ? data2[3:0] :
           (digit_select == 3'd3) ? data3[3:0] :
           (digit_select == 3'd4) ? data4[3:0] :
           (digit_select == 3'd5) ? data5[3:0] :
           4'hF; // 如果 digit_select 超出范围 (理论上不会发生)，默认显示 'F'

    // 实例化十六进制到七段码的解码器
    hex_to_7seg decoder_inst (
        .hex_digit(data_for_current_digit),
        .seg_pattern(seg_pattern_from_decoder)
    );

    // 驱动输出 'seg' 和 'sel'
    // 这个 always @(*) 块确保 seg 和 sel 根据内部状态（digit_select, seg_pattern_from_decoder）立即更新
    always @(*) begin
        seg = seg_pattern_from_decoder; // 从解码器获取共阳极段码

        // sel 是低电平有效的位选信号
        case (digit_select)
            3'd0: sel = 6'b111110; // 选中 DIG1
            3'd1: sel = 6'b111101; // 选中 DIG2
            3'd2: sel = 6'b111011; // 选中 DIG3
            3'd3: sel = 6'b110111; // 选中 DIG4
            3'd4: sel = 6'b101111; // 选中 DIG5
            3'd5: sel = 6'b011111; // 选中 DIG6
            default: sel = 6'b111111; // 所有数码管都不选 (全灭)
        endcase
    end

endmodule
