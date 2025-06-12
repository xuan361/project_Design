`timescale 1ns / 1ps

module Single_CPU_tb();

    // 实例化 Single_CPU 模块
    reg CLK;
    reg RESET; // 模拟物理按键
    reg uart_rx_pin;   // 模拟串口输入
    reg wait_transport;

    wire led1; // 连接到顶层模块的LED输出
    wire led2; // 连接到顶层模块的LED输出
    wire led3; // 连接到顶层模块的LED输出
    wire led4; // 连接到顶层模块的LED输出

    wire [6:0] seg;
    wire [5:0] sel; 


    // 实例化顶层模块
    SingleCPU uut (
        .CLK(CLK),
        .RESET(RESET),
        .wait_transport(wait_transport),
        .uart_rx_pin(uart_rx_pin),
        .led1(led1),
        .led2(led2),
        .led3(led3),
        .led4(led4),
        .seg(seg),
        .sel(sel)
    );

    always begin
        #5 CLK = ~CLK;  // 每 5 ns 反转一次时钟信号，周期为 10 ns
        wait_transport = 0;
    end

    initial begin
        CLK = 0;
        RESET = 1;

        #5 RESET = 0;

        #5 RESET = 1;


        #200;

        #10 $finish;

    end

endmodule