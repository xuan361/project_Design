opcode_map = {
    'jal':  '0000',
    'jalr': '0001',
    'beq':  '0010',
    'ble':  '0011',
    'lb':   '0100',
    'lw':   '0101',
    'sb':   '0110',
    'sw':   '0111',
    'add':  '1000',
    'sub':  '1001',
    'and':  '1010',
    'or':   '1011',
    'lui':  '1110',
    'addi': '1100',
    'subi': '1101'
}

def reg_bin(reg_name):
    return format(int(reg_name[1:]), '04b')

def imm_bin(val, bits=4):
    return format((val + (1 << bits)) % (1 << bits), f'0{bits}b')

def assemble_line(line):
    tokens = line.replace(',', '').replace('(', ' ').replace(')', '').split()
    if not tokens:
        return None

    instr = tokens[0]
    if instr == 'jal':
        rd = reg_bin(tokens[1])
        imm = imm_bin(int(tokens[2]))
        bin_code = imm + rd + opcode_map[instr]
    elif instr == 'jalr':
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2])
        imm = imm_bin(int(tokens[3]))
        bin_code = imm + rs + rd + opcode_map[instr]
    elif instr in ['addi', 'subi']:
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2])
        imm = imm_bin(int(tokens[3]))
        bin_code = imm + rs + rd + opcode_map[instr]
    elif instr in ['beq', 'ble']:
        rs1 = reg_bin(tokens[1])
        rs2 = reg_bin(tokens[2])
        imm = imm_bin(int(tokens[3]))
        bin_code = rs2 + rs1 + imm + opcode_map[instr]
    elif instr in ['lb', 'lw']:
        rd = reg_bin(tokens[1])
        imm = imm_bin(int(tokens[2]))
        rs = reg_bin(tokens[3])
        bin_code = imm + rs + rd + opcode_map[instr]
    elif instr in ['sb', 'sw']:
        rt = reg_bin(tokens[1])
        imm = imm_bin(int(tokens[2]))
        rs = reg_bin(tokens[3])
        bin_code = imm + rs + rt + opcode_map[instr]
    elif instr in ['add', 'sub', 'and', 'or']:
        rd = reg_bin(tokens[1])
        rs1 = reg_bin(tokens[2])
        rs2 = reg_bin(tokens[3])
        bin_code = rs2 + rs1 + rd + opcode_map[instr]
    elif instr == 'lui':
        rd = reg_bin(tokens[1])
        imm = format(int(tokens[2], 16), '08b')
        bin_code = imm + rd + opcode_map[instr]
    else:
        raise ValueError(f"Unknown instruction: {instr}")

    return bin_code.zfill(16)

def assemble_program(asm_lines):
    bin_lines = []
    for line in asm_lines:
        if not line.strip() or line.strip().startswith("//"):
            continue
        try:
            bin_code = assemble_line(line.strip())
            formatted = '_'.join([bin_code[i:i+4] for i in range(0, 16, 4)])
            bin_lines.append(formatted)
        except Exception as e:
            print(f"Error on line: '{line.strip()}': {e}")
    return bin_lines

if __name__ == '__main__':
    asm = [
        'jal r1, 0',
        'jalr r1, r3, 6',
        'addi r3, r1, 2',
        'subi r4, r1, -2',
        'beq r3, r4, -6',
        'ble r3, r5, 0',
        'add r5, r3, r4',
        'sub r6, r3, r4',
        'sb r5, 2(r6)',
        'sw r5, 4(r6)',
        'lb r7, 4(r6)',
        'lw r8, 2(r6)',
        'and r9, r5, r6',
        'or r10, r5, r6',
        'lui r11, 0xA1'
    ]
    output = assemble_program(asm)
    print("\n机器码输出 ：")
    for line in output:
        print(line)

    with open('machine_code_output.txt', 'w') as f:
        for line in output:
            f.write(line + '\n')
