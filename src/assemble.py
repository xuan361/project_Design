import re

# 操作码映射
opcode_map = {
    "jal":  "0000", "jalr": "0001", "beq": "0010", "ble": "0011",
    "lb":   "0100", "lw":   "0101", "sb":  "0110", "sw":  "0111",
    "add":  "1000", "sub":  "1001", "and": "1010", "or":  "1011",
    "addi": "1100", "subi": "1101", "lui": "1110"
}

# 寄存器映射
reg_map = {f"r{i}": f"{i:04b}" for i in range(16)}

# 转换为补码二进制
def to_bin(val, bits):
    if val < 0:
        val = (1 << bits) + val
    return format(val, f"0{bits}b")[-bits:]

# 汇编单行
def assemble_line(line):
    line = line.split("#")[0].strip()  # 去除注释
    if not line:        #处理空行
        return None

    tokens = re.split(r'[,\s()]+', line.strip())
    instr = tokens[0]

    if instr == "jal":
        rd = reg_map[tokens[1]]
        imm = to_bin(int(tokens[2]), 4)
        return imm + rd + opcode_map[instr]

    elif instr == "jalr":
        rd = reg_map[tokens[1]]
        rs1 = reg_map[tokens[2]]
        imm = to_bin(int(tokens[3]), 4)
        return imm + rs1 + rd + opcode_map[instr]

    elif instr in ["addi", "subi"]:

        rd = reg_map[tokens[1]]

        rs = reg_map[tokens[2]]

        imm = to_bin(int(tokens[3]), 4)

        return imm + rs + rd + opcode_map[instr]

    elif instr in ["lb", "lw"]:

    # 支持语法：lb rd, imm(rs)

        rd = reg_map[tokens[1]]

        imm = to_bin(int(tokens[2]), 4)

        rs = reg_map[tokens[3]]

        return imm + rs + rd + opcode_map[instr]

    elif instr in ["beq", "ble"]:
        rs1 = reg_map[tokens[1]]
        rt = reg_map[tokens[2]]
        offset = to_bin(int(tokens[3]), 4)
        return rt + rs1 + offset + opcode_map[instr]

    elif instr in ["sb", "sw"]:
        rt = reg_map[tokens[1]]
        rs = reg_map[tokens[3]]
        imm = to_bin(int(tokens[2]), 4)
        return rt + rs + imm + opcode_map[instr]

    elif instr in ["add", "sub", "and", "or"]:
        rd = reg_map[tokens[1]]
        rs1 = reg_map[tokens[2]]
        rt = reg_map[tokens[3]]
        return rt + rs1 + rd + opcode_map[instr]

    elif instr == "lui":
        rd = reg_map[tokens[1]]
        imm = int(tokens[2], 16) if tokens[2].startswith("0x") else int(tokens[2])
        return to_bin(imm, 8) + rd + opcode_map[instr]

    else:
        raise ValueError(f"Unknown instruction: {instr}")



# 汇编整个程序
def assemble_program(lines, output_format="bin"):
    machine_code = []
    for line in lines:
        try:
            bin_code = assemble_line(line)
            if bin_code:
                if output_format == "bin":
                    # 分组成 4 位一组，加入 Verilog 风格前缀
                    formatted = "16'b" + '_'.join([bin_code[i:i+4] for i in range(0, 16, 4)])
                    machine_code.append(formatted)
                elif output_format == "hex":
                    machine_code.append(f"{int(bin_code, 2):04X}")
        except Exception as e:
            print(f"Error on line: '{line}': {e}")
    return machine_code


# 示例用法
if __name__ == "__main__":
    asm_code = [
        "jal r1, 0",
        "jalr r1, r3, 6",
        "addi r3, r1, 2",
        "subi r4, r1, -2",
        "beq r3, r4, -6",
        "ble r3, r5, 0",
        "add r5, r3, r4",
        "sub r6, r3, r4",
        "sb r5, 2(r6)",
        "sw r5, 4(r6)",
        "lb r7, 4(r6)",
        "lw r8, 2(r6)",
        "and r9, r5, r6",
        "or r10, r5, r6",
        "lui r11, 0xA1"
    ]

    output = assemble_program(asm_code, output_format="bin")

    print("机器码输出 ：")
    for line in output:
        print(line)

