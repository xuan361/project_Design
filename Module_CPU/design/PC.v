
// 16位寄存器，低电平复位信号有效
// PC：CLK上升沿触发，更改指令地址
module PC(
    input  CLK,     //时钟
    input  RESET,   //复位信号，低电平有效
    input PCWre,    //PC写使能.如果为0，PC不更改;
    input  [15:0] newAddress,   //PC的新指令地址
    
    output reg [15:0] currentAddress    //当前指令地址
);

    initial begin
        currentAddress = 0;
    end

    always @(posedge CLK or negedge RESET)
    begin
        if(!RESET) begin
            currentAddress <= 0;
        end
        else if(PCWre)
            currentAddress <= newAddress;
        else
            currentAddress <= currentAddress;
    end

endmodule