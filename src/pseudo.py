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
register_map = {f"r{i}": format(i, '04b') for i in range(16)}


#  添加伪指令展开函数
def expand_pseudo_instruction(line, labels):
    tokens = line.replace(',', '').split()
    if not tokens:
        return [line]
    instr = tokens[0]

    if instr == 'li':
        rd, imm = tokens[1], int(tokens[2], 0)
        hi = (imm >> 8) & 0xFF
        lo = imm & 0xFF
        return [f'lui {rd}, {hi}', f'addi {rd}, {rd}, {lo}']

    elif instr == 'la':
        rd, label = tokens[1], tokens[2]
        addr = labels.get(label, 0)
        hi = (addr >> 8) & 0xFF
        lo = addr & 0xFF
        return [f'lui {rd}, {hi}', f'addi {rd}, {rd}, {lo}']

    elif instr == 'bge':
        rs1, rs2, label = tokens[1], tokens[2], tokens[3]
        return [f'ble {rs2}, {rs1}, {label}']  # bge rs1, rs2 → ble rs2, rs1

    elif instr == 'j':
        label = tokens[1]
        return [f'jal r0, {label}']

    return [line]


# 解析指令为机器码
def parse_instruction(line, labels, pc):
    tokens = line.replace(',', '').split()
    if not tokens:
        return None
    op = tokens[0]

    if op == 'lui':
        rd = register_map[tokens[1]]
        imm = format(int(tokens[2], 0), '08b')
        return f"16'b{opcode_map[op]}_{imm[:4]}_{rd}_{imm[4:]}"

    if op in ('jal', 'jalr'):
        if op == 'jal':
            rd = register_map[tokens[1]]
            imm = format(int(tokens[2], 0), '04b')
            return f"16'b{opcode_map[op]}_{imm}_{rd}_0000"
        else:
            rd = register_map[tokens[1]]
            rs1 = register_map[tokens[2]]
            imm = format(int(tokens[3], 0), '04b')
            return f"16'b{opcode_map[op]}_{imm}_{rs1}_{rd}"

    if op in ('addi', 'subi'):
        rd = register_map[tokens[1]]
        rs = register_map[tokens[2]]
        imm = format(int(tokens[3], 0) & 0xFF, '08b')
        return f"16'b{opcode_map[op]}_{imm[:4]}_{rs}_{rd}_{imm[4:]}"

    if op in ('beq', 'ble'):
        rs1 = register_map[tokens[1]]
        rs2 = register_map[tokens[2]]
        offset = labels.get(tokens[3], int(tokens[3])) - (pc + 2)
        imm = format(offset & 0x0F, '04b')
        return f"16'b{opcode_map[op]}_{rs1}_{rs2}_{imm}"

    if op in ('add', 'sub', 'and', 'or'):
        rs1 = register_map[tokens[1]]
        rs2 = register_map[tokens[2]]
        rd = register_map[tokens[3]]
        return f"16'b{opcode_map[op]}_{rs1}_{rs2}_{rd}"

    if op in ('lb', 'lw'):
        rd = register_map[tokens[1]]
        offset, rs1 = re.findall(r'(-?\d+)\((r\d+)\)', tokens[2])[0]
        imm = format(int(offset) & 0x0F, '04b')
        rs = register_map[rs1]
        return f"16'b{opcode_map[op]}_{imm}_{rs}_{rd}"

    if op in ('sb', 'sw'):
        rs2 = register_map[tokens[1]]
        offset, rs1 = re.findall(r'(-?\d+)\((r\d+)\)', tokens[2])[0]
        imm = format(int(offset) & 0x0F, '04b')
        rs = register_map[rs1]
        return f"16'b{opcode_map[op]}_{imm}_{rs}_{rs2}"

    return None


# 汇编主函数
def assemble_program(lines):
    labels = {}
    pc = 0
    processed_lines = []

    # 第一遍：收集标签地址
    for line in lines:
        line = line.split('#')[0].strip()
        if ':' in line:
            label = line.replace(':', '').strip()
            labels[label] = pc
        elif line:
            pc += 2

    # 第二遍：翻译指令
    pc = 0
    for line in lines:
        line = line.split('#')[0].strip()
        if not line or line.endswith(':'):
            continue

        #  插入伪指令处理逻辑
        expanded_lines = expand_pseudo_instruction(line, labels)

        for ex_line in expanded_lines:
            instr = parse_instruction(ex_line, labels, pc)
            if instr:
                processed_lines.append(instr)
                pc += 2

    return processed_lines


# 示例调用
if __name__ == '__main__':
    with open('program.asm',encoding='utf-8') as f:
        lines = f.readlines()
    binary = assemble_program(lines)
    print("机器码输出：")
    for code in binary:
        print(code)
