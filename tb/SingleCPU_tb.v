`timescale 1ns / 1ps

module Single_CPU_tb();

    reg clk;
    reg RESET;

    wire [3:0] op;
    wire [3:0] rs;
    wire [3:0] rt;
    wire [3:0] rd;

    wire [15:0] ReadData1;
    wire [15:0] ReadData2;
    wire [15:0] WriteData;
    wire [15:0] DataOut;
    wire [15:0] currentAddress;
    wire [15:0] result;

    // 实例化 Single_CPU 模块
    SingleCPU uut (
        .CLK(CLK),
        .RESET(RESET),

        .op(op),
        .rs(rs),
        .rt(rt),
        .rd(rd),

        .ReadData1(ReadData1),
        .ReadData2(ReadData2),
        .WriteData(WriteData),
        .DataOut(DataOut),
        .currentAddress(currentAddress),
        .result(result)
    );

    always begin
        #5 clk = ~clk;  // 每 5 ns 反转一次时钟信号，周期为 10 ns
    end

    initial begin
        clk = 0;
        RESET = 0;

        #5 RESET = 1;


        #100;

        #10 $finish;

    end

endmodule