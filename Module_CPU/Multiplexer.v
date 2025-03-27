
// Multiplexer2：二路选择器
// Multiplexer3：三路选择器


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