opcode_map = {
    "jal": "0000", "jalr": "0001", "beq": "0010", "ble": "0011",
    "lb": "0100", "lw": "0101", "sb": "0110", "sw": "0111",
    "add": "1000", "sub": "1001", "and": "1010", "or": "1011",
    "lui": "1110", "addi": "1100", "subi": "1101"
}

reg_map = {f"r{i}": f"{i:04b}" for i in range(16)}


def to_bin(val, bits):
    if val < 0:
        val = (1 << bits) + val
    return format(val, f"0{bits}b")[-bits:]


def assemble_line(line):
    tokens = line.replace(',', '').split()
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

    elif instr in ["addi", "subi", "lb", "lw"]:
        rd = reg_map[tokens[1]]
        rs = reg_map[tokens[2]]
        imm = to_bin(int(tokens[3]), 4)
        return imm + rs + rd + opcode_map[instr]

    elif instr in ["beq", "ble"]:
        rs1 = reg_map[tokens[1]]
        rt = reg_map[tokens[2]]
        offset = to_bin(int(tokens[3]), 4)
        return rt + rs1 + offset + opcode_map[instr]

    elif instr in ["sb", "sw"]:
        rt = reg_map[tokens[1]]
        offset, rs = tokens[2].replace(")", "").split("(")
        rs = reg_map[rs]
        imm = to_bin(int(offset), 4)
        return rt + rs + imm + opcode_map[instr]

    elif instr in ["add", "sub", "and", "or"]:
        rd = reg_map[tokens[1]]
        rs1 = reg_map[tokens[2]]
        rt = reg_map[tokens[3]]
        return rt + rs1 + rd + opcode_map[instr]

    elif instr == "lui":
        rd = reg_map[tokens[1]]
        imm = to_bin(int(tokens[2], 16), 8)
        return imm + rd + opcode_map[instr]

    else:
        raise ValueError(f"Unknown instruction: {instr}")


# 示例测试
lines = [
    "jal r1, 4",
    "jalr r1, r3, 6",
    "addi r3, r1, 2",
    "beq r3, r4, -6",
    "sb r5, 2(r6)",
    "lui r11, 0xA1"
]

for line in lines:
    binary = assemble_line(line)
    print(f"{line:30} => {binary}  => 0x{int(binary, 2):04X}")
