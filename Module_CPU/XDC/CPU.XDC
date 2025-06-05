# 时钟与复位约束
# 50MHz系统时钟约束（对应核心板50MHz晶振）
create_clock -name CLK -period 20.000 [get_ports CLK]
set_property PACKAGE_PIN W19   [get_ports CLK]       ;# 核心板50MHz时钟输入
set_property IOSTANDARD LVCMOS33 [get_ports CLK]

# 复位信号约束（对应底板复位按键）
set_property PACKAGE_PIN Y19   [get_ports RESET]     ;# 底板机械复位按键
set_property IOSTANDARD LVCMOS33 [get_ports RESET]
set_property PULLUP true        [get_ports RESET]    ;# 按键上拉配置

# 暂停控制信号（预留扩展IO）
set_property PACKAGE_PIN Y18    [get_ports wait_transport]       ;# 扩展IO CN3_引脚29
set_property IOSTANDARD LVCMOS33 [get_ports wait_transport]
set_property PULLDOWN true      [get_ports wait_transport]       ;# 默认下拉防干扰



# 串口与控制信号约束
# UART接收引脚（对应底板Type-C串口）
set_property PACKAGE_PIN W17    [get_ports uart_rx_pin]  ;# CH340G_RX
set_property IOSTANDARD LVCMOS33 [get_ports uart_rx_pin]
set_property PULLUP true        [get_ports uart_rx_pin]  ;# 串口默认上拉



# LED指示灯约束（对应Mini底板LED1-LED4）
set_property PACKAGE_PIN N20    [get_ports led1]      ;# LED1（用户指示灯）
set_property PACKAGE_PIN M20    [get_ports led2]      ;# LED2（用户指示灯）
set_property PACKAGE_PIN N22    [get_ports led3]      ;# LED3（用户指示灯）
set_property PACKAGE_PIN M22    [get_ports led4]      ;# LED4（暂停状态指示）
set_property IOSTANDARD LVCMOS33 [get_ports {led1 led2 led3 led4}]
set_property DRIVE 8            [get_ports {led1 led2 led3 led4}] ;# 高亮度驱动



# 设置数码管引脚的约束
set_property PACKAGE_PIN K18 [get_ports dig1]
set_property IOSTANDARD LVCMOS33 [get_ports dig1]

set_property PACKAGE_PIN K16 [get_ports dig2]
set_property IOSTANDARD LVCMOS33 [get_ports dig2]

set_property PACKAGE_PIN L16 [get_ports dig3]
set_property IOSTANDARD LVCMOS33 [get_ports dig3]

set_property PACKAGE_PIN G20 [get_ports dig4]
set_property IOSTANDARD LVCMOS33 [get_ports dig4]

set_property PACKAGE_PIN H20 [get_ports dig5]
set_property IOSTANDARD LVCMOS33 [get_ports dig5]

set_property PACKAGE_PIN H18 [get_ports dig6]
set_property IOSTANDARD LVCMOS33 [get_ports dig6]

set_property PACKAGE_PIN U22 [get_ports out[0]]
set_property IOSTANDARD LVCMOS33 [get_ports out[0]]

set_property PACKAGE_PIN P19 [get_ports out[1]]
set_property IOSTANDARD LVCMOS33 [get_ports out[1]]

set_property PACKAGE_PIN W21 [get_ports out[2]]
set_property IOSTANDARD LVCMOS33 [get_ports out[2]]

set_property PACKAGE_PIN V22 [get_ports out[3]]
set_property IOSTANDARD LVCMOS33 [get_ports out[3]]

set_property PACKAGE_PIN AB20 [get_ports out[4]]
set_property IOSTANDARD LVCMOS33 [get_ports out[4]]

set_property PACKAGE_PIN W22 [get_ports out[5]]
set_property IOSTANDARD LVCMOS33 [get_ports out[5]]

set_property PACKAGE_PIN AA20 [get_ports out[6]]
set_property IOSTANDARD LVCMOS33 [get_ports out[6]]

# # 六位数码管约束
# # 位选信号（低有效，DIG1-DIG6）
# set_property PACKAGE_PIN K18   [get_ports {sel[0]}]  ;# DIG1 位选
# set_property PACKAGE_PIN K16   [get_ports {sel[1]}]  ;# DIG2 位选
# set_property PACKAGE_PIN L16   [get_ports {sel[2]}]  ;# DIG3 位选
# set_property PACKAGE_PIN G20   [get_ports {sel[3]}]  ;# DIG4 位选
# set_property PACKAGE_PIN H20   [get_ports {sel[4]}]  ;# DIG5 位选
# set_property PACKAGE_PIN H18   [get_ports {sel[5]}]  ;# DIG6 位选

# # 段选信号（共阳，低有效 a-g=seg[6:0]）
# set_property PACKAGE_PIN AA20    [get_ports {seg[6]}]  ;# a段
# set_property PACKAGE_PIN W22    [get_ports {seg[5]}]  ;# b段
# set_property PACKAGE_PIN AB20    [get_ports {seg[4]}]  ;# c段
# set_property PACKAGE_PIN V22    [get_ports {seg[3]}]  ;# d段
# set_property PACKAGE_PIN W21   [get_ports {seg[2]}]  ;# e段
# set_property PACKAGE_PIN P19    [get_ports {seg[1]}]  ;# f段
# set_property PACKAGE_PIN U22   [get_ports {seg[0]}]  ;# g段

# # 数码管公共配置
# set_property IOSTANDARD LVCMOS33 [get_ports {sel[*] seg[*]}]
# set_property DRIVE 8            [get_ports {sel[*] seg[*]}]  ;# 8mA驱动增强亮度
# set_property PULLUP true        [get_ports {sel[*]}]         ;# 位选默认高电平