.data
array: .word 64, 34, -25, 12, 22, 11, 90
array_size: .byte 7
.align 4

.text
_start:
    la r4, array          # s0 -> r4
    lb r5, array_size     # s1 -> r5

    # 外层循环计数器 (i)
    li r6, 0              # t0 = r6

outer_loop:
    # 检查是否完成所有外层循环 (i < ARRAY_LEN - 1)
    addi r7, r5, -1       # t1 = r7
    bge r6, r7, end_sort

    # （此处省略内部排序逻辑）
    j outer_loop

end_sort:
    # 排序完成，进入无限循环
    j end_sort
