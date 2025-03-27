
// DataMemory：用于内存存储，内存读写

module DataMemory(
    input clk,
    input wmem,           //读写信号，1为写，0为读
    input [15:0] DAddress,  //地址
    input [15:0] DataIn,     //输入数据
    input memc,             //控制写入字节数，memc=0为1字节，memc=1为两个字节。

    output reg [15:0] DataOut  //输出数据
); 

    // 模拟内存，以8位为一字节存储，共64字节
    reg[7:0] memory[0:63]; 
    wire [15:0] DAddress_Standard = (DAddress >> 1) << 1;

    // 初始化内存
    integer i;
    initial 
    begin
        for(i = 0; i < 64; i = i + 1) memory[i] = 8'b0;
    end

    //  读写内存
    always @(posedge clk)
    begin
        // 写入内存,先写高八位，再写低八位
        if (wmem) begin
            if(memc == 1) begin
                memory[DAddress_Standard] = DataIn[15:8];
                memory[DAddress_Standard + 1] = DataIn[7:0];
            end
            else begin
                memory[DAddress] = DataIn[7:0];
            end
        end
        // 读取内存
        else begin
            if(memc == 1) begin
                DataOut[15:8] = memory[DAddress_Standard];
                DataOut[7:0] = memory[DAddress_Standard + 1];
            end
            else begin
                DataOut[7:0] = memory[DAddress];
                DataOut[15:8] = 8'b0;
            end
        end
    end
    


endmodule