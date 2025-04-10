
// Multiplexer21：二路选择器
// Multiplexer31：三路选择器
// Multiplexer41：四路选择器


// 选择立即数，还是B_data写入到ALU
module Multiplexer21 (
    input control,
    input [15:0] in0,
    input [15:0] in1,
    output [15:0] out

);
    assign out = control ? in1 : in0;
endmodule


module Multiplexer31 (
    input [1:0] PCsrc,
    input [15:0] currentAddress_2,
    input [15:0] currentAddress_immediate,
    input [15:0] result,

    output reg[15:0] newAddress
);
    always @(*)begin
        case(PCsrc)
            0:  newAddress = currentAddress_2;
            1:  newAddress = currentAddress_immediate;
            2:  newAddress = result;
        endcase

    end


endmodule

// 选择写回寄存器的数据
// 0：把ALU的运算结果传回
// 1：把数据存储器的数据传回 
// 2:把currentAddress_2传回 
// 3：把立即数左移八位后的数据传回
module Multiplexer41 (
    input [1:0] control,
    input [15:0] in0,
    input [15:0] in1,
    input [15:0] in2,
    input [15:0] in3,

    output reg[15:0] out
);
    always @(*)begin
        case(control)
            0:  out = in0;
            1:  out = in1;
            2:  out = in2;
            3:  out = in3;
        endcase
    end

endmodule