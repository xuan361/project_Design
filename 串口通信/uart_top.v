`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 2024/12/07 21:16:28
// Design Name: 
// Module Name: uart_top
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


module uart_top(
      input wire sys_clk , //系统时钟50MHz
      input wire sys_rst_n , //全局复位
      input wire rx, //串口接收数据
      output wire tx, //串口发送数据
      
      output wire led1,
      output wire led2,
      output wire led3,
      output wire led4,
      output wire[6:0] out
    );

   parameter BPS =  9600;   //发送波特率
   parameter CNT_BIT_CLK_MAX = 5208;      //“时钟-bit”计数器


   wire [7:0] po_data;
   wire  po_flag;

   reg [3:0] cnt_1;
   reg [31:0] division_data;

   wire [15:0] shang;
   wire [15:0] yushu;
   reg [31:0] division_out_data;

   reg division_out_flag;
   reg [3:0] cnt_2;
   reg  [7:0] pi_data;
   reg  pi_flag;


   wire done;
   reg start;
   wire tx_done;


// initial begin
//    cnt_1 <= 4'b0;
//    cnt_2 <= 4'b0;
//    division_data <= 32'b0;
//    pi_data <= 8'b0;
//    pi_flag <= 0;
//    start <= 1;
// end

uart_rx
 #(
    .BPS(BPS),
    .CNT_BIT_CLK_MAX(CNT_BIT_CLK_MAX)
 )
 uart_rx_inst
 (
    .sys_clk (sys_clk ), //input sys_clk
    .sys_rst_n (sys_rst_n ), //input sys_rst_n
    .rx (rx ), //input rx

    .po_data (po_data ), //output [7:0] po_data
    .po_flag (po_flag ) //output po_flag
 );

// 接收模块输出的数据传送到计算模块
   always@(posedge sys_clk or negedge sys_rst_n)
   begin
      if(!sys_rst_n)begin
         cnt_1 <= 4'b0;
         division_data <= 0;
      end
      else if(po_flag == 1 && cnt_1 < 4) begin
         case(cnt_1)
         0: division_data[15:8] <= po_data[7:0];   //被除数
         1: division_data[7:0] <= po_data[7:0];
         2: division_data[31:24] <= po_data[7:0];  //除数
         3: division_data[23:16] <= po_data[7:0];
         endcase

         cnt_1 <= cnt_1 + 1;
      end
      else if(cnt_1 == 4) begin
         start <= 0;
         cnt_1 <= 0;
      end
      else
         start <= 1;
   end



// 计算模块
division division_inst
(
   .sys_clk (sys_clk), //input sys_clk
   .sys_rst_n (sys_rst_n ), //input sys_rst_n
   .start (start), 
   .dividend(division_data[15:0]),
   .divisor(division_data[31:16]),

   .shang (shang[15:0]), 
   .yushu (yushu[15:0]), 
   .done(done),
   .led1(led1),
   .led2(led2),
   .led3(led3),
   .led4(led4),
   .out(out)
);   


// 计算模块数据传送到输出模块
   always@(posedge sys_clk or negedge sys_rst_n)
      if(!sys_rst_n) begin
         division_out_data <= 0;
         division_out_flag <= 0;
         cnt_2 <= 4'b0;
         pi_flag <= 0;
      end
      else if(done == 1)begin
         division_out_data[31:16] <= shang[15:0];
         division_out_data[15:0] <= yushu[15:0];
         division_out_flag <= 1;
      end
      else if(division_out_flag == 1 && cnt_2 < 4 && tx_done == 1 && pi_flag == 0) begin
         case(cnt_2)
         0: pi_data[7:0] <= division_out_data[31:24];
         1: pi_data[7:0] <= division_out_data[23:16];
         2: pi_data[7:0] <= division_out_data[15:8];
         3: pi_data[7:0] <= division_out_data[7:0];
         default:
            pi_data[7:0] <= 8'd0;
         endcase
         
         cnt_2 <= cnt_2 + 1;
         pi_flag <= 1;
      end
      else if(cnt_2 == 4)begin
         cnt_2 <= 0;
         division_out_flag <= 0;
         pi_flag <= 0;
      end
      else
         pi_flag <= 0;



   // always@(posedge sys_clk or negedge sys_rst_n)
   // begin
   //    if(!sys_rst_n)begin
   //       cnt_2 <= 4'b0;
   //    end
   //    else if(done == 1 && cnt_2 < 4 && tx_done == 1 && pi_flag == 0) begin
   //       case(cnt_2)
   //       0: pi_data[7:0] <= division_out_data[31:24];
   //       1: pi_data[7:0] <= division_out_data[23:16];
   //       2: pi_data[7:0] <= division_out_data[15:8];
   //       3: pi_data[7:0] <= division_out_data[7:0];
   //       endcase

   //       cnt_2 <= cnt_2 + 1;
   //       pi_flag <= 1;
   //    end
   //    else if(cnt_2 == 4)begin
   //       cnt_2 <= 0;
   //       // done <= 0;
   //       pi_flag <= 0;
   //    end
   //    else
   //       pi_flag <= 0;
   // end

//输出模块
uart_tx
#(
   .BPS(BPS),
   .CNT_BIT_CLK_MAX(CNT_BIT_CLK_MAX)
)
uart_tx_inst
(
   .sys_clk (sys_clk ), //input sys_clk
   .sys_rst_n (sys_rst_n ), //input sys_rst_n
   .pi_data (pi_data), //input [7:0] pi_data
   .pi_flag (pi_flag), //input pi_flag

   .tx (tx), //output tx
   .tx_done(tx_done)
);


endmodule



