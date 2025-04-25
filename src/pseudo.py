import re

#六条伪指令la lb li addi bge j,但其实 lb addi是已有的指令
#只有la li bge j是新建的


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
    'lui': '1110',
    'addi': '1100',
    'subi': '1101'
}

#寄存器映射
register_alias = {
    'r0': 0, 'ra': 1, 'sp': 2,
    **{f'a{i}': i + 3 for i in range(13)},  # a0-a12 -> r3-r15
    # r0为恒0寄存器，r1为返回地址寄存器ra，r2为栈指针寄存器sp，其余为运算寄存器a0-a12(即r3-r15)
}


def reg_bin(reg_name):
    if reg_name in register_alias:
        reg_num = register_alias[reg_name]

    elif reg_name.startswith('r'):
        reg_num = int(reg_name[1:])

    else:
        raise ValueError(f"Unknown register name: {reg_name}")

    return format(reg_num, '04b')


def imm_bin(val, bits=4):
    return format((val + (1 << bits)) % (1 << bits), f'0{bits}b')


def strip_comments(line):
    return line.split('//')[0].split('#')[0].split('\t')[0].strip()


# 伪指令
def expand_pseudo_instructions(lines):
    expanded = []
    label_map = {}
    pc = 0

    for line in lines:
        clean = strip_comments(line)

        if not clean:
            continue

        if ':' in clean:
            label, rest = clean.split(':', 1)
            label_map[label.strip()] = pc
            clean = rest.strip()

            if not clean:
                continue
        tokens = clean.split()

        if not tokens:
            continue

        instr = tokens[0]

        if instr == 'li':
            rd, imm = tokens[1], int(tokens[2])
            upper = (imm >> 4) & 0xFF
            lower = imm & 0xF
            expanded.append(f'lui {rd}, 0x{upper:X}')

            if lower != 0:
                expanded.append(f'addi {rd}, {rd}, {lower}')
                pc += 2

            else:
                pc += 1

        elif instr == 'la':
            rd, label = tokens[1], tokens[2]
            expanded.append(f'lui {rd}, {label}')  # 后续替换地址
            pc += 1

        elif instr == 'j':
            label = tokens[1]
            expanded.append(f'jal r0, {label}')
            pc += 1

        elif instr == 'bge':
            rs1, rs2, label = tokens[1], tokens[2], tokens[3]
            expanded.append(f'ble {rs2}, {rs1}, {label}')
            pc += 1

        else:
            expanded.append(clean)
            pc += 1

    return expanded, label_map


def resolve_labels(expanded_lines, label_map):
    resolved = []

    for idx, line in enumerate(expanded_lines):
        tokens = line.replace(',', '').split()

        if not tokens:
            continue

        instr = tokens[0]

        if instr in ['ble', 'beq', 'jal']:
            try:
                imm = int(tokens[-1])
                resolved.append(line)

            except ValueError:
                label = tokens[-1]
                offset = label_map[label] - idx - 1
                tokens[-1] = str(offset)
                resolved.append(' '.join(tokens))

        elif instr == 'lui' and tokens[2] in label_map:
            addr = label_map[tokens[2]] << 4
            tokens[2] = f'0x{(addr >> 4):X}'
            resolved.append(' '.join(tokens))

        else:
            resolved.append(line)

    return resolved


def assemble_line(line):
    tokens = line.replace(',', '').replace('(', ' ').replace(')', '').split()
    instr = tokens[0]

    if instr == 'jal':
        rd = reg_bin(tokens[1])
        imm = imm_bin(int(tokens[2]))
        return (imm + rd + opcode_map[instr]).zfill(16)

    elif instr == 'jalr':
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2])
        imm = imm_bin(int(tokens[3]))
        return imm + rs + rd + opcode_map[instr]

    elif instr in ['addi', 'subi']:
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2])
        imm = imm_bin(int(tokens[3]))
        return imm + rs + rd + opcode_map[instr]

    elif instr in ['beq', 'ble']:
        rs1 = reg_bin(tokens[1])
        rs2 = reg_bin(tokens[2])
        imm = imm_bin(int(tokens[3]))
        return rs2 + rs1 + imm + opcode_map[instr]

    elif instr in ['lb', 'lw']:
        rd = reg_bin(tokens[1])
        imm = imm_bin(int(tokens[2]))
        rs = reg_bin(tokens[3])
        return imm + rs + rd + opcode_map[instr]

    elif instr in ['sb', 'sw']:
        rt = reg_bin(tokens[1])
        imm = imm_bin(int(tokens[2]))
        rs = reg_bin(tokens[3])
        return imm + rs + rt + opcode_map[instr]

    elif instr in ['add', 'sub', 'and', 'or']:
        rd = reg_bin(tokens[1])
        rs1 = reg_bin(tokens[2])
        rs2 = reg_bin(tokens[3])
        return rs2 + rs1 + rd + opcode_map[instr]

    elif instr == 'lui':
        rd = reg_bin(tokens[1])
        imm = format(int(tokens[2], 16), '08b')
        return imm + rd + opcode_map[instr]

    else:
        raise ValueError(f"Unknown instruction: {instr}")


# 汇编
def assemble_program(lines):
    expanded, label_map = expand_pseudo_instructions(lines)
    resolved = resolve_labels(expanded, label_map)
    machine_code = []

    for line in resolved:
        try:
            bin_code = assemble_line(line.strip())
            formatted = '_'.join([bin_code[i:i + 4] for i in range(0, 16, 4)])
            machine_code.append(formatted)

        except Exception as e:
            print(f"Error on line: '{line.strip()}': {e}")

    return machine_code


if __name__ == '__main__':

    # 注意！！从 program.txt 文件读取汇编指令，若文件命名不同则及时更改
    with open('program.txt', 'r') as f:
        lines = f.readlines()

    # 汇编生成机器码
    output = assemble_program(lines)

    # 打印机器码到终端
    print("\n机器码输出 ：")
    for line in output:
        print(line)

    # 输出机器码到文件 machine_code_output.txt
    with open('machine_code_output.txt', 'w') as f:
        for line in output:
            f.write(line + '\n')