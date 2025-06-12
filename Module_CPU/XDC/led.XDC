# 设置时钟引脚的约束
# FPGA_CLK 时钟引脚
set_property PACKAGE_PIN W19 [get_ports CLK]
set_property IOSTANDARD LVCMOS33 [get_ports CLK]

# 设置复位引脚的约束
# RESET 复位引脚
set_property PACKAGE_PIN Y19 [get_ports RESET]
set_property IOSTANDARD LVCMOS33 [get_ports RESET]


# led 复位引脚
set_property PACKAGE_PIN N20 [get_ports led1]  
set_property PACKAGE_PIN M20 [get_ports led2]
set_property PACKAGE_PIN N22 [get_ports led3]
set_property PACKAGE_PIN M22 [get_ports led4] 
set_property IOSTANDARD LVCMOS33 [get_ports {led1 led2 led3 led4}]
set_property DRIVE 8 [get_ports {led1 led2 led3 led4}]
