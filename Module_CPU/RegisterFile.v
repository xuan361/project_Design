

//RegisterFile：储存寄存器组，并根据地址对寄存器组进行读写

module RegisterFile(
    input CLK,
    input RegWre,   // 写使能信号，为1时，在时钟上升沿写入
    input [3:0] rs,            // 源寄存器地址
    input [3:0] rt,            // 目标寄存器地址
    input [3:0] WriteReg,      // 将数据写入的寄存器端口，其地址来源rt或rd字段
    
    input [15:0] WriteData,    // 写入寄存器的数据输入端口
    output [15:0] ReadData1,   // rs寄存器数据输出端口
    output [15:0] ReadData2    // rt寄存器数据输出端口
);

    reg [15:0] register[0:15];  // 寄存器组

    // 初始时，将16个寄存器全部赋值为0
    integer i;
    initial 
     begin
        for(i = 0; i < 16; i = i + 1) register[i] <= 0;
     end

    //assign 保证 ReadData1始终与rs地址的寄存器值相同，ReadData2始终与rt地址的寄存器值相同
    assign ReadData1 = register[rs];
    assign ReadData2 = register[rt];

    // 当写使能信号为1时，在时钟上升沿写入
    always @(posedge CLK)
    begin
        // 如果寄存器不为0，并且RegWre为真，写入数据
        if (RegWre && WriteReg != 0) begin
            register[WriteReg] = WriteData;
        end
    end

endmodule