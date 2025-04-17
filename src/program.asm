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
