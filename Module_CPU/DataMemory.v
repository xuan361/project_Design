
// DataMemory：用于内存存储，内存读写
module DataMemory(
    input CLK,
    input RESET,
    input wmem,           //读写信号，1为写，0为读
    input [15:0] DAddress,  //地址
    input [15:0] DataIn,     //输入数据
    input memc,             //控制写入字节数，memc=0为1字节，memc=1为两个字节。
    input [15:0] DataFromROM,

    output reg [15:0] DataOut,  //输出数据
    output reg led1,     //数码管显示
    output reg led2,
    output reg led3,
    output reg led4,
    output reg [15:0] ROMDataAddress,
    output [6:0] seg,// 段选信号（共阳，a-g=seg[6:0]）
    output [5:0] sel // 位选信号（低有效，DIG1-DIG6）
); 
    localparam RAMStartAddress = 16'h1000;
    localparam ledAddr = 16'h2000;
    localparam digitAddress = 16'h3000;

    // 模拟内存，以8位为一字节存储，共64字节
    reg[7:0] RAM[0:63]; 
    reg[7:0] digit[0:5];

    wire [15:0] RAM_address_standard;   // RAM标准地址（一个字）
    wire [15:0] RAMaddress;      //RAM地址（单字节）

    assign RAMaddress = {4'b0, DAddress[11:0]};     //assign使用前一定要声明变量类型
    /*
    如果您在Verilog中对一个未声明的标识符直接使用 assign 语句（即这个标识符出现在 assign 的左边，作为被赋值的目标），
    具体取决于您的Verilog编译器/仿真器的设置，特别是 default_nettype 指令：
    default_nettype wire (默认或未指定时常见行为):
    如果 default_nettype 设置为 wire（或者您没有在文件顶部指定 default_nettype，很多工具会默认此行为），那么这个未声明的标识符会被隐式地声明为一个1位的 wire。
    */


    assign RAM_address_standard = (RAMaddress >> 1) << 1;

    // 数码管对应输入数据
    always @(*) begin
        digit[0] <= RAM[0];
        digit[1] <= RAM[1];
        digit[2] <= RAM[2];
        digit[3] <= RAM[3];
        digit[4] <= RAM[4];
        digit[5] <= RAM[5];
    end

    // 初始化内存
    integer i;
    initial 
    begin
        for(i = 0; i < 64; i = i + 1) RAM[i] = 8'b0;
    end

    //  读写内存
    always @(posedge CLK or negedge RESET)
    begin
        if (!RESET) begin
            for(i = 0; i < 64; i = i + 1) RAM[i] <= 8'b0;
            led1 <= 1'b0;    led2 <= 1'b0;    led3 <= 1'b0;    led4 <= 1'b0;
        end
        else if(DAddress == ledAddr) begin
            led1 = DataIn[0];
        end
        else if(DAddress == ledAddr + 1) begin
            led2 = DataIn[0];
        end
        else if(DAddress == ledAddr + 2) begin
            led3 = DataIn[0];
        end
        else if(DAddress == ledAddr + 3) begin
            led4 = DataIn[0];
        end
        else if(DAddress >= RAMStartAddress && DAddress < ledAddr)begin
            // 写入内存,先写高八位，再写低八位
            //小端模式：传入的数据低位要放在索引值小的存储单元里
            if (wmem) begin
                if(memc == 1) begin
                    RAM[RAM_address_standard + 1] = DataIn[15:8];
                    RAM[RAM_address_standard] = DataIn[7:0];
                end
                else begin
                    RAM[RAMaddress] = DataIn[7:0];
                end
            end
        end
    end
    
    // 读取内存(内存到寄存器)
    always@(*)begin
        if (DAddress < RAMStartAddress) begin
                ROMDataAddress = DAddress;
                DataOut = DataFromROM;
        end
        else begin
            if(memc == 1) begin
                DataOut[15:8] = RAM[RAM_address_standard + 1];
                DataOut[7:0] = RAM[RAM_address_standard];
            end
            else begin
                DataOut[7:0] = RAM[RAMaddress];
                DataOut[15:8] = 8'b0;
            end
        end

    end   

six_digit_7seg_display display(CLK, RESET, digit[0], digit[1], digit[2], digit[3],digit[4], digit[5], seg, sel);

endmodule