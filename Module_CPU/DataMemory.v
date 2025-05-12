
// DataMemory：用于内存存储，内存读写
//  仍存在的问题：DataOut和memory在仿真图像中一直为0
module DataMemory(
    input CLK,
    input RESET,
    input wmem,           //读写信号，1为写，0为读
    input [15:0] DAddress,  //地址
    input [15:0] DataIn,     //输入数据
    input memc,             //控制写入字节数，memc=0为1字节，memc=1为两个字节。

    output reg [15:0] DataOut,  //输出数据
    output reg dig1,     //数码管显示
    output reg dig2,
    output reg dig3,
    output reg dig4
); 
    localparam ledAddr = 16'h2000;

    // 模拟内存，以8位为一字节存储，共64字节
    reg[7:0] memory[0:63]; 

    wire [15:0] DAddress_Standard;
    assign DAddress_Standard = (DAddress >> 1) << 1;

    // 初始化内存
    integer i;
    initial 
    begin
        for(i = 0; i < 64; i = i + 1) memory[i] = 8'b0;
    end

    //  读写内存
    always @(posedge CLK or negedge RESET)
    begin
        if (!RESET) begin
            for(i = 0; i < 64; i = i + 1) memory[i] = 8'b0;
            dig1 = 1'b0;
            dig2 = 1'b0;
            dig3 = 1'b0;
            dig4 = 1'b0;
        end
        else if(DAddress == ledAddr) begin
            dig1 = DataIn[0];
        end
        else if(DAddress == ledAddr + 1) begin
            dig2 = DataIn[0];
        end
        else if(DAddress == ledAddr + 2) begin
            dig3 = DataIn[0];
        end
        else if(DAddress == ledAddr + 3) begin
            dig4 = DataIn[0];
        end
        else begin
            // 写入内存,先写高八位，再写低八位
            //小端模式：传入的数据低位要放在索引值小的存储单元里
            if (wmem) begin
                if(memc == 1) begin
                    memory[DAddress_Standard + 1] = DataIn[15:8];
                    memory[DAddress_Standard] = DataIn[7:0];
                end
                else begin
                    memory[DAddress] = DataIn[7:0];
                end
            end
        end
    end
    
    // 读取内存
    always@(*)begin
        if(memc == 1) begin
            DataOut[15:8] = memory[DAddress_Standard + 1];
            DataOut[7:0] = memory[DAddress_Standard];
        end
        else begin
            DataOut[7:0] = memory[DAddress];
            DataOut[15:8] = 8'b0;
        end

    end   


endmodule