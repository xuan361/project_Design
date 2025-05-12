import re      # 用于正则表达式处理，例如去除注释
import sys     # 可用于处理命令行参数
import os      # 用于文件路径处理（如果你读写文件）

# 将汇编语言的指令名称映射为对应的机器码
# 原始操作码表
opcode_map = {
    'jal': '0000',
    'jalr': '0001',
    'beq': '0010',
    'ble': '0011',
    'lb': '0100',
    'lw': '0101',
    'sb': '0110',
    'sw': '0111',
    'add': '1000',
    'sub': '1001',
    'and': '1010',
    'or': '1011',
    'addi': '1100',
    'subi': '1101',
    'lui': '1110'
}

#寄存器映射
register_alias = {
    'r0': 0, 'ra': 1, 'sp': 2,
    **{f'a{i}': i + 3 for i in range(13)},  # a0-a12 -> r3-r15
    # **{...} 是把这个字典“展开”到前面的字典里
    # r0为恒0寄存器，r1为返回地址寄存器ra，r2为栈指针寄存器sp，其余为运算寄存器a0-a12(即r3-r15)
}

# === 将寄存器名转为二进制字符串 ===
def reg_bin(reg_name):
    if reg_name in register_alias:
        reg_num = register_alias[reg_name]
    elif reg_name.startswith('r') and reg_name[1:].isdigit():
        reg_num = int(reg_name[1:])
    else:
        raise ValueError(f"未知寄存器: {reg_name}")
    return format(reg_num, '04b')  # 4位二进制字符串
    # 将一个整数 reg_num 转换为长度为4位的二进制字符串，如果不足4位就前面补0。
def imm_bin(val, bits=4):
    return format((val + (1 << bits)) % (1 << bits), f'0{bits}b')


def strip_comments(line):
    return line.split('//')[0].split('#')[0].split('\t')[0].strip()


# === 立即数转为二进制（支持负数） ===
def imm_bin(value, bits=4):
    value = int(value)
    return format((value + (1 << bits)) % (1 << bits), f'0{bits}b')
    # 1 << bits 是1左移bits位，即 2的bits次方
    # 返回的是立即数的补码形式，即去掉符号位

# === 去除注释和空白 ===
def strip_comments(line):
    return re.split(r'#|//', line)[0].strip()
    # 1. re.split(r'#|//', line)
    # 使用正则表达式将字符串 line 按照 # 或 // 进行分割。
    # re.split(...) 返回的是一个列表，前面是实际代码，后面是注释内容
    #strip() 去除字符串左右的空格、制表符、换行符等，保持整洁。

    