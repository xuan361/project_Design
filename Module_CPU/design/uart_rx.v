`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/12/07 15:27:59
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

/* rx位宽为1bit，PC机通过串口调试助手往FPGA发8bit数据时，
FPGA通过串口线rx一位一位地接收，从最低位到最高位依次接收，
最后在FPGA里面位拼接成8比特数据。

*/

// 接收模块(8位有效数据，即一个字节)
module uart_rx
#(
    parameter BPS =  9600,   //发送波特率
    CLK_FRE = 50_000_000,    //系统时钟，频率50MHZ
    CNT_BIT_CLK_MAX = 5208,      //“时钟-bit”计数器
    CNT_BYTE_BIT = 10        //“bit-字节”计数器
)
(
    input wire sys_clk,      //系统时钟，频率50MHZ,即电平切换周期为20ns
    input wire sys_rst_n,    //全局复位，低电平有效
    input wire rx,     //串口接收数据，高电平空闲，低电平工作。

    output reg [7:0] po_data,   //输出完整的8位有效数据
    output reg po_flag        //输出数据有效标志


);
    reg rx_reg1 ;           //第一级寄存器，寄存器空闲状态复位为1
    reg rx_reg2 ;           //第二级寄存器，寄存器空闲状态复位为1
    reg rx_reg3 ;           //第三级寄存器和第二级寄存器共同构成下降沿检测
    reg start_nedge ;       //检测到下降沿时start_nedge产生一个时钟的高电平
    reg work_en ;           //接收数据工作使能信号
    reg [12:0] baud_cnt;    //波特率计数器计数，从0计数到5207
    reg bit_flag ;          //高电平表示数据可以被取走
    reg [3:0] bit_cnt ;     //有效数据个数计数器
    reg [7:0] rx_data ;     //输入数据进行移位
    reg rx_flag ;           //输入数据移位完成时rx_flag拉高一个时钟的高电平

//插入两级寄存器进行数据同步，用来消除亚稳态
//rx_reg1:第一级寄存器，寄存器空闲状态复位为1
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        rx_reg1 <= 1'b1;
    else
        rx_reg1 <= rx;
//rx_reg2:第二级寄存器，寄存器空闲状态复位为1
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        rx_reg2 <= 1'b1;
    else
        rx_reg2 <= rx_reg1;
//rx_reg3:第三级寄存器和第二级寄存器共同构成下降沿检测
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        rx_reg3 <= 1'b1;
    else
        rx_reg3 <= rx_reg2;

//start_nedge:检测到下降沿时start_nedge产生一个时钟的高电平
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        start_nedge <= 1'b0;
    else if((~rx_reg2) && (rx_reg3))    //rx_reg2为0，rx_reg3为1
        start_nedge <= 1'b1;
    else
    start_nedge <= 1'b0;

//work_en:接收数据工作使能信号，遇到开始信号转为高电平，遇到复位信号和结束状态变为低电平。
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        work_en <= 1'b0;
    else if(start_nedge == 1'b1)
        work_en <= 1'b1;
    else if((bit_cnt == 4'd8) && (bit_flag == 1'b1))
        work_en <= 1'b0;

//baud_cnt:波特率计数器计数，从0计数到5207
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        baud_cnt <= 13'b0;
    else if((baud_cnt == CNT_BIT_CLK_MAX - 1) || (work_en == 1'b0))
        baud_cnt <= 13'b0;
    else if(work_en == 1'b1)
        baud_cnt <= baud_cnt + 1;

//bit_flag:当baud_cnt计数器计数到中间数时采样的数据最稳定，
//此时拉高一个标志信号表示数据可以被取走
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        bit_flag <= 1'b0;
    else if(baud_cnt == CNT_BIT_CLK_MAX/2 - 1)
        bit_flag <= 1'b1;
    else
        bit_flag <= 1'b0;

//bit_cnt:有效数据个数计数器，当8个有效数据（不含起始位和停止位）
//都接收完成后计数器清零
always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        bit_cnt <= 4'b0;
    else if((bit_cnt == 8) && (bit_flag == 1))
        bit_cnt <= 4'b0;
    else if(bit_flag == 1)
        bit_cnt <= bit_cnt + 1;

 //rx_data:输入数据进行移位
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        rx_data <= 8'b0;
    else if((bit_cnt >= 4'd1)&&(bit_cnt <= 4'd8)&&(bit_flag == 1'b1))
        rx_data <= {rx_reg3, rx_data[7:1]}; //先传低位
        

//rx_flag:输入数据移位完成时rx_flag拉高一个时钟的高电平
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        rx_flag <= 1'b0;
    else if((bit_cnt == 4'd8) && (bit_flag == 1'b1))
        rx_flag <= 1'b1;
    else
        rx_flag <= 1'b0;        

//po_data:输出完整的8位有效数据
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        po_data <= 8'b0;
    else if(rx_flag == 1'b1)
        po_data <= rx_data;

 //po_flag:输出数据有效标志（比rx_flag延后一个时钟周期，为了和po_data同步）
 always@(posedge sys_clk or negedge sys_rst_n)
    if(sys_rst_n == 1'b0)
        po_flag <= 1'b0;
    else
        po_flag <= rx_flag;

endmodule
