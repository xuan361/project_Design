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

#增强对输入的汇编语言的读取能力，实现有引号（' 或 "），在有逗号 有多空格 有空行 有注释的情况下也能自动清理并汇编干净
def clean_asm_lines(raw_lines):
    cleaned = []
    for line in raw_lines:
        # 去除注释部分（从 // 开始）
        line = line.split('//')[0]

        # 去除开头和结尾空格
        line = line.strip()

        # 去除开头和结尾的单引号或双引号
        line = line.strip("'\"")

        # 如果最后是逗号，也去掉
        if line.endswith(','):
            line = line[:-1]

        # 如果非空行才保留
        if line:
            cleaned.append(line)
    return cleaned


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

    # 注意！！！！从 program.txt 文件读取汇编指令，若文件命名不同则及时更改
    with open('program.txt', 'r') as f:
        raw_lines = f.readlines()
    # 清理输入内容
    asm = clean_asm_lines(raw_lines)

    # 汇编生成机器码
    output = assemble_program(asm)


    #打印机器码到终端
    print("\n机器码输出 ：")
    for line in output:
        print(line)


    #输出机器码到文件 machine_code_output.txt
    with open('machine_code_output.txt', 'w') as f:
        for line in output:
            f.write(line + '\n')
