// 目的：认识指令的具体含义并尝试自己写出对应的机器码
#机器码顺序：偏移量（imm/offset）_目的操作数_源操作数_操作指令

0.jal rd,imm：
'''****
jump and link
# 将PC的值加上2，结果写入rd寄存器，rd默认为r1，同时将PC的值设置为PC加上符号位拓展的imm，
	即PC=PC+sext(imm)。
#小端模式，small endian mode
    0000 0100(imm) 0001(rd) 0000(jal) 
机器码：16’b0000_0100_0001_0000

'''

1.jalr rd,rs1,imm：
'''
#将PC的值加上2，结果写入rd寄存器，rd默认为r1，同时将PC值设置为寄存器rs1的值加上符号位拓展的imm，
	即PC=rs1+sext(imm)。
# 0100(imm) 0011(rs1) 0001(rd) 0001(jalr)
# 机器码：16’b0100_0011_0001_0001
'''

2.beq rs1,rs2,offset
'''
如果寄存器rs1(a1:0100)和rs2(a2:0101)的值相等，那么跳转，偏移量为offset(6),否则执行下一条(pc = pc + 2)
不需要写入寄存器
举例：
if a1 == a2:
	PC = PC + 6
else:
	pc = pc + 2
'''
机器码：16'b 0110_0101_0100_0010

3.ble rd, rs2, offset
'''
如果寄存器rs1(a1)的值小于等于rs2(a2)的值，则跳转，偏移量为offset(6),否则执行下一条(pc = pc + 2)
不需要写入寄存器
举例：
if a1 <= a2:
	PC = pc + 6
else:
	pc = pc + 2
'''
机器码： 16'b0110_0101_0100_0011

4.lb rd, offset(rs1)
'''
load byte
从寄存器rs1中获得基础地址(a1:0100)，a1加上偏移量offset(6)后得到内存地址，然后将内存地址存放的一字节数据加载到寄存器rd(a2)中
举例:
ad = a1 + 6
a2 = (ad)
'''
机器码：16'b0110_0101_0100_0100

5.lw rd, offset(rs1)
'''
load word
从寄存器rs1中获得基础地址(a1:0100)，a1加上偏移量offset(6)后得到内存地址，然后将内存地址存放的一个字（2字节）数据加载到寄存器rd(a2)中
举例:
ad = a1 + 6
a2 = (ad)
'''
机器码：16'b0110_0101_0100_0101

6.sb rs1, offset(rs2)
'''
store byte
从寄存器rs2(a2)中获得基址，a2加上偏移量offset(6)后得到内存地址，然后将寄存器rs1(a1:0100)中存放的一字节数据存放到内存地址中
举例:
ad = a2 + 6
(ad) = a1
'''
机器码：16'b0110_0101_0100_0110

7.sw rs1, offset(rs2)
'''
store word
从寄存器rs2(a2)中获得基址，a2加上偏移量offset(6)后得到内存地址，然后将寄存器rs1(a1:0100)中存放的一个字（2字节）数据存放到内存地址中
举例:
ad = a2 + 6
(ad) = a1
'''
机器码：16'b0110_0101_0100_0111

8.add rd,rs1,rs2
'''
将寄存器rs1(r0)和rs2(r1)中的值相加，然后存放到rd(r2)中
add r2, r0, r1
举例：
r2 = r0 + r1
'''
机器码：16'b0010_0001_0000_1000

9.sub rd,rs1,rs2
'''
将寄存器rs1(r0)和rs2(r1)中的值相减，然后存放到rd(r2)中
sub r2, r0, r1
举例：
r2 = r0 - r1
'''
机器码：16'b0010_0001_0000_1001


10.and rd,rs1,rs2
'''
将寄存器rs1(r0)和rs2(r1)进行逻辑并运算，然后将结果存放到rd(r2)中
and r2, r0, r1
举例：
r2 = r0 & r1
'''
机器码：16'b0010_0001_0000_1010

11.or rd,rs1,rs2
'''
将寄存器rs1(r0)和rs2(r1)进行逻辑或运算，然后将结果存放到rd(r2)中
or r2, r0, r1
举例：
r2 = r0 | r1
'''
机器码：16'b0010_0001_0000_1011

12.addi rd,rs1,imm
'''
将寄存器rs1(r0)和imm(6)中的值相加，然后存放到rd(r1)中
举例：
r2 = r0 + 6
'''
机器码：16'b0110_0001_0000_1100

13.subi rd,rs1,imm
'''
将寄存器rs1(r0)的值和imm(6)相减，然后存放到rd(r2)中
举例：
r2 = r0 - 6
'''
机器码：16'b0110_0010_0000_1101


14.andi rd,rs1,imm
'''
将寄存器rs1(r0)和imm(6)进行逻辑并运算，然后将结果存放到rd(r2)中
举例：
r2 = r0 & imm
'''
机器码：16'b0110_0010_0000_1110

15.ori rd,rs1,imm
'''
将寄存器rs1(r0)和imm(6)进行逻辑或运算，然后将结果存放到rd(r2)中
举例：
r2 = r0 | 6
'''
机器码：16'b0110_0010_0000_1111
