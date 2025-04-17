4、给定一个汇编程序，制定汇编语法规则，写一个软件将汇编指令翻译成机器指令。再根据汇编语法规则，写一个整数排序程序。

16个16位通用寄存器：r0-r15，其中r0为恒0寄存器，r1为返回地址寄存器ra，r2为栈指针寄存器sp，其余为运算寄存器a0-a12(即r3-r15)，其中a0还作为保存函数参数或返回值。

// jal->addi->subi->beq->jalr->ble->add->sub->sb->sw->lb->lw->and->or->andi->ori
    0000_0100_0001_0000 
  //  imm(4),   rd,  jal    (r1) = pc + 2, pc = pc + 4  //此时(r1) = 2, pc =4

    0110_0011_0001_0001     (r1) = pc + 2, pc = (r3) + 6  //此时(r1) = 4, pc = 10
  //imm,  rs,  rd,  jalr

    0010_0001_0011_1100     
  //imm   rs,  rd,  addi    (r3) = (r1) + 2     // 此时(r3) = 4, pc = 6

    1110_0001_0100_1101
  //imm,  rs,  rd,  subi    (r4) = (r1) - (-2)   //此时(r4) = 4, pc = 8

    0100_0011_1010_0010     (r3) == (r4) ? pc = pc - 6 : pc = pc + 2  //此时pc = 2
  //rt,  rs, offset, beq
    
    0101_0011_0000_0011
  //rt,  rs, offset, ble    (r3) <= (r5) ? pc = pc  : pc = pc + 2     // pc = 12
    
    0100_0011_0101_1000
  //rt,   rs,  rd,  add    (r5) = (r3) + (r4)   //此时(r5) = 8
    
    0100_0011_0110_1001
  //rt,   rs,  rd,  sub    (r6) = (r3) - (r4)   //此时(r6) = 0

    0101_0110_0010_0110
  //rt,  rs,  imm,  sb      ad = (r6) + 2   (ad) = (r5)     //此时存储单元[2] = 8

    0101_0110_0100_0111
  //rt,  rs,  imm,  sw      ad = (r6) + 4   (ad) = (r5)     //此时存储单元[4] = 8   存储单元[5] = 0    

    0100_0110_0111_0100
  //imm,  rs,  rd,  lb      ad = (r6) + 4   (r7) = (ad)     //此时(r7) = 0000_1000

    0010_0110_1000_0101
  //imm,  rs,  rd,  lw      ad = (r6) + 2   (r8) = (ad)     //此时(r8) = 0000_1000_0000_0000

    0110_0101_1001_1010
  //rt,   rs,  rd,  and    (r9) = (r5) && (r6)  //此时r9 = 0

    0110_0101_1010_1011
  //rt,   rs,  rd,  or     (r10) = (r5) || (r6)  //此时r10 = 8 即(0000_0000_0000_1000)

    1010_0001_1011_1110
  //    imm,    rd,  lui      (r11) = imm << 8  //此时r11 = 1010_0001_0000_0000





.data
array: .word 64, 34, -25, 12, 22, 11, 90 #
array_size: .byte 7 #
.align 4

.text
_start:
     la s0, array
     lb s1, array_size

    # 外层循环计数器 (i)
    li t0, 0                 # t0 = i = 0
outer_loop:
    # 检查是否完成所有外层循环 (i < ARRAY_LEN - 1)
    addi t1, s1, -1          # t1 = ARRAY_LEN - 1
    bge t0, t1, end_sort     # if i >= ARRAY_LEN-1, 结束
。。。
end_sort:
    # 排序完成，进入无限循环
    j end_sort
![image](https://github.com/user-attachments/assets/4ca96b3a-1bd9-4bc8-afb8-7a0dc91bafd3)




.data
array: .word 64, 34, -25, 12, 22, 11, 90 #
array_size: .byte 7 #
.align 4

.text
_start:
 #把 data section 从 flash 搬运到 ram 中
 la a0, _data_lma
 la a1, _data_start
 la a2, _data_end
 bge a1, a2, begin
 。。。
begin:#开始
    la s0, array
    lb s1, array_size
。。。
end_sort:
    # 排序完成，进入无限循环
    j end_sort
_data_lma:
![image](https://github.com/user-attachments/assets/a62f89ea-bf69-4c39-851d-d19d08be64f6)

