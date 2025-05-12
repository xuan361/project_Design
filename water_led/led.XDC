# 设置时钟引脚的约束
# FPGA_CLK 时钟引脚
set_property PACKAGE_PIN W19 [get_ports CLK]
set_property IOSTANDARD LVCMOS33 [get_ports CLK]

# 设置复位引脚的约束
# RESET 复位引脚
set_property PACKAGE_PIN Y19 [get_ports RESET]
set_property IOSTANDARD LVCMOS33 [get_ports RESET]


# 设置数码管引脚的约束
set_property PACKAGE_PIN K18 [get_ports dig1]
set_property IOSTANDARD LVCMOS33 [get_ports dig1]

set_property PACKAGE_PIN K16 [get_ports dig2]
set_property IOSTANDARD LVCMOS33 [get_ports dig2]

set_property PACKAGE_PIN L16 [get_ports dig3]
set_property IOSTANDARD LVCMOS33 [get_ports dig3]

set_property PACKAGE_PIN G20 [get_ports dig4]
set_property IOSTANDARD LVCMOS33 [get_ports dig4]

# set_property PACKAGE_PIN H20 [get_ports dig5]
# set_property IOSTANDARD LVCMOS33 [get_ports dig5]

# set_property PACKAGE_PIN H18 [get_ports dig6]
# set_property IOSTANDARD LVCMOS33 [get_ports dig6]

# set_property PACKAGE_PIN U22 [get_ports out[0]]
# set_property IOSTANDARD LVCMOS33 [get_ports out[0]]

# set_property PACKAGE_PIN P19 [get_ports out[1]]
# set_property IOSTANDARD LVCMOS33 [get_ports out[1]]

# set_property PACKAGE_PIN W21 [get_ports out[2]]
# set_property IOSTANDARD LVCMOS33 [get_ports out[2]]

# set_property PACKAGE_PIN V22 [get_ports out[3]]
# set_property IOSTANDARD LVCMOS33 [get_ports out[3]]

# set_property PACKAGE_PIN AB20 [get_ports out[4]]
# set_property IOSTANDARD LVCMOS33 [get_ports out[4]]

# set_property PACKAGE_PIN W22 [get_ports out[5]]
# set_property IOSTANDARD LVCMOS33 [get_ports out[5]]

# set_property PACKAGE_PIN AA20 [get_ports out[6]]
# set_property IOSTANDARD LVCMOS33 [get_ports out[6]]
