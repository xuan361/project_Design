`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/12/07 20:24:52
// Design Name: 
// Module Name: uart_tx
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

// 发送模块
module uart_tx
#(
    parameter BPS =  9600,   //发送波特率
    CLK_FRE = 50_000_000,    //系统时钟，频率50MHZ
    CNT_BIT_CLK_MAX = 5208      //“时钟-bit”计数器
)
(
    input wire sys_clk,      //系统时钟，频率50MHZ,即电平切换周期为20ns
    input wire sys_rst_n,    //全局复位，低电平有效
    input wire [7:0] pi_data , //模块输入的8bit数据
    input wire pi_flag , //并行数据有效标志信号，高电平工作，低电平空闲

    output reg tx, //空闲状态时为高电平
    output reg tx_done  //完成信号
);

    reg [12:0] baud_cnt;    //波特率计数器计数，从0计数到5207
    reg bit_flag;       //当baud_cnt计数器计数到1时让bit_flag拉高一个时钟的高电平
    reg [3:0] bit_cnt ;     //数据位数个数计数
    reg work_en ;   // 接收数据工作使能信号

 //work_en:接收数据工作使能信号
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        work_en <= 1'b0;
    else if(pi_flag == 1'b1) begin
        work_en <= 1'b1;
    end
    else if((bit_flag == 1'b1) && (bit_cnt == 4'd10))
        work_en <= 1'b0;

 //baud_cnt:波特率计数器计数，从0计数到5207
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        baud_cnt <= 13'b0;
    else if((baud_cnt == CNT_BIT_CLK_MAX - 1) || (work_en == 1'b0))
        baud_cnt <= 13'b0;
    else if(work_en == 1'b1)
        baud_cnt <= baud_cnt + 1'b1;

 //bit_flag:当baud_cnt计数器计数到1时让bit_flag拉高一个时钟的高电平
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        bit_flag <= 1'b0;
    else if(baud_cnt == 13'd1)
        bit_flag <= 1'b1;
    else
        bit_flag <= 1'b0;

 //bit_cnt:数据位数个数计数，10个有效数据（含起始位和停止位）到来后计数器清零
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        bit_cnt <= 4'b0;
    else if((bit_flag == 1'b1) && (bit_cnt == 4'd10))
        bit_cnt <= 4'b0;
    else if((bit_flag == 1'b1) && (work_en == 1'b1))
        bit_cnt <= bit_cnt + 1'b1;


 //tx:输出数据在满足rs232协议（起始位为0，停止位为1）的情况下一位一位输出
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0) 
        tx <= 1'b1; //空闲状态时为高电平
    else if(bit_flag == 1'b1)
        case(bit_cnt)
            0 : tx <= 1'b0;
            1 : tx <= pi_data[0];
            2 : tx <= pi_data[1];
            3 : tx <= pi_data[2];
            4 : tx <= pi_data[3];
            5 : tx <= pi_data[4];
            6 : tx <= pi_data[5];
            7 : tx <= pi_data[6];
            8 : tx <= pi_data[7];
            9 : tx <= 1'b1;
            default : tx <= 1'b1;
        endcase


 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        tx_done <= 1'b1;
    else if(bit_flag == 1 && bit_cnt == 10)
        tx_done <= 1'b1;
    else if(pi_flag == 1'b1)
        tx_done <= 1'b0;    // 未完成

endmodule
