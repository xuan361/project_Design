# 操作码映射表
opcode_map = {
    "jal": "0000",
    "jalr": "0001",
    "beq": "0010",
    "ble": "0011",
    "lb": "0100",
    "lw": "0101",
    "sb": "0110",
    "sw": "0111",
    "add": "1000",
    "sub": "1001",
    "and": "1010",
    "or": "1011",
    "lui": "1110"
}

# 寄存器映射表
register_map = {
    "r0": 0, "r1": 1, "r2": 2, "r3": 3, "r4": 4, "r5": 5, "r6": 6, "r7": 7,
    "r8": 8, "r9": 9, "r10": 10, "r11": 11, "r12": 12, "r13": 13, "r14": 14, "r15": 15
}

# 生成机器码的函数
def assemble_instruction(instruction):
    parts = instruction.split()
    opcode = parts[0]
    if opcode not in opcode_map:
        raise ValueError(f"未知指令: {opcode}")

    opcode_bin = opcode_map[opcode]
    machine_code = ""

    # 处理每种指令
    if opcode == "jal":
        rd = register_map[parts[1]]
        imm = int(parts[2])
        machine_code = f"{opcode_bin}{imm:04b}{rd:04b}"

    elif opcode == "jalr":
        rd = register_map[parts[1]]
        rs1 = register_map[parts[2]]
        imm = int(parts[3])
        machine_code = f"{opcode_bin}{imm:04b}{rs1:04b}{rd:04b}"

    elif opcode == "addi":
        rd = register_map[parts[1]]
        rs1 = register_map[parts[2]]
        imm = int(parts[3])
        machine_code = f"{opcode_bin}{imm:04b}{rs1:04b}{rd:04b}"

    elif opcode == "subi":
        rd = register_map[parts[1]]
        rs1 = register_map[parts[2]]
        imm = int(parts[3])
        machine_code = f"{opcode_bin}{imm:04b}{rs1:04b}{rd:04b}"

    elif opcode in ["beq", "ble"]:
        rs1 = register_map[parts[1]]
        rs2 = register_map[parts[2]]
        offset = int(parts[3])
        machine_code = f"{opcode_bin}{rs1:04b}{rs2:04b}{offset:08b}"

    elif opcode in ["add", "sub", "and", "or"]:
        rd = register_map[parts[1]]
        rs1 = register_map[parts[2]]
        rs2 = register_map[parts[3]]
        machine_code = f"{opcode_bin}{rs1:04b}{rs2:04b}{rd:04b}"

    elif opcode in ["lb", "lw", "sb", "sw"]:
        rt = register_map[parts[1]]
        rs1 = register_map[parts[2]]
        offset = int(parts[3])
        machine_code = f"{opcode_bin}{rs1:04b}{rt:04b}{offset:08b}"

    elif opcode == "lui":
        rd = register_map[parts[1]]
        imm = int(parts[2])
        machine_code = f"{opcode_bin}{imm:08b}{rd:04b}"

    return machine_code

# 汇编函数
def assemble_program(program):
    machine_codes = []
    for line in program:
        line = line.strip()
        if line and not line.startswith("#"):  # 忽略空行和注释
            machine_code = assemble_instruction(line)
            machine_codes.append(machine_code)
    return machine_codes

# 示例程序
program = [
    "jal r1 4",              # 机器码：0000 0100 0001 0000
    "jalr r1 r3 6",          # 机器码：0001 0110 0011 0001
    "addi r3 r1 2",          # 机器码：0010 0001 0011 1100
    "subi r4 r1 -2",         # 机器码：1110 0001 0100 1101
    "beq r3 r4 -6",          # 机器码：0100 0011 1010 0010
    "ble r3 r5 2",           # 机器码：0101 0011 0000 0011
    "add r5 r3 r4",          # 机器码：0100 0011 0101 1000
    "sub r6 r3 r4",          # 机器码：0100 0011 0110 1001
    "sb r6 r5 2",            # 机器码：0101 0110 0010 0110
    "sw r6 r5 4",            # 机器码：0101 0110 0100 0111
    "lb r7 r6 4",            # 机器码：0100 0110 0111 0100
    "lw r8 r6 2",            # 机器码：0010 0110 1000 0101
    "and r9 r5 r6",          # 机器码：0110 0101 1001 1010
    "or r10 r5 r6",          # 机器码：0110 0101 1010 1011
    "lui r11 16128",         # 机器码：1010 0001 1011 1110
]

# 汇编并输出机器码
machine_codes = assemble_program(program)
for code in machine_codes:
    print(code)
