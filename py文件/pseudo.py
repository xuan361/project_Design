import re

# 原始操作码表 (保持不变)
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

# 寄存器映射
register_alias = {
    'r0': 0, 'ra': 1, 'sp': 2,
    **{f'a{i}': i + 3 for i in range(13)},
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
    # 对于负立即数，确保它们在指定位数内以二进制补码形式正确表示
    if val < 0:
        val = (1 << bits) + val # Calculates two's complement for negative numbers
    return format(val % (1 << bits), f'0{bits}b')


def strip_comments(line): # (稍作调整)
    # 优先移除 // 和 # 类型的注释，然后是 \t 分割，最后去除首尾空格
    line_no_double_slash = line.split('//')[0]
    line_no_hash = line_no_double_slash.split('#')[0]
    # 如果你的注释风格是 tab 后面的都是注释，这行是必要的
    # 但如果 tab 可能出现在指令内部（不推荐），则这行可能过于激进
    # 为了安全，如果tab可能在指令操作数之间，则这行应更细致处理或移除
    line_no_tab_comment = line_no_hash.split('\t')[0] # 假设tab后的内容为注释或无关紧要
    return line_no_tab_comment.strip()


# 修改后的伪指令扩展函数
def expand_pseudo_instructions(lines):
    expanded_instructions = []
    label_map = {}  # 用于存储标签名到其在 expanded_instructions 中的索引
    pc = 0  # 当前指令在 expanded_instructions 中的索引

    for line_number, raw_line in enumerate(lines):
        # 1. 清理行：移除注释和首尾空格
        #    标签定义中的冒号':'会在这里被保留
        line_for_label_detection = strip_comments(raw_line)

        if not line_for_label_detection: # 如果行变为空，则跳过
            continue

        instruction_part = line_for_label_detection
        # 2. 检测和处理标签定义
        if ':' in line_for_label_detection:
            label_name, rest_of_line = line_for_label_detection.split(':', 1)
            label_name = label_name.strip()

            if not label_name:
                # 通常空的标签名是错误的，但这里我们选择忽略它并处理行剩下的部分
                print(f"Warning on line {line_number + 1}: Empty label name found. Processing rest of line: '{rest_of_line.strip()}'")
            elif ' ' in label_name or '\t' in label_name or ',' in label_name:
                print(f"Warning on line {line_number + 1}: Label name '{label_name}' contains whitespace or comma. This might lead to errors. Ensure labels are single words.")
            # 你可能想在这里添加更多标签名有效性检查 (e.g., re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label_name))

            if label_name: # 只有当标签名非空时才处理
                if label_name in label_map:
                    raise ValueError(f"Error on line {line_number + 1}: Duplicate label definition '{label_name}'")
                label_map[label_name] = pc  # 标签指向下一条有效指令的索引

            instruction_part = rest_of_line.strip() # 获取冒号后的指令部分

        if not instruction_part:  # 如果行仅包含标签定义，或者处理后指令部分为空
            continue

        # 3. 处理指令（可能是伪指令或真实指令）
        # 注意：这里的tokens是基于空格分割的，逗号可能仍附着在操作数上
        # 后续的 resolve_labels 和 assemble_line 中的 .replace(',', '') 会处理这些逗号
        tokens = instruction_part.split()
        if not tokens: # 如果分割后没有token（例如，只有空格的instruction_part）
            continue

        op = tokens[0]

        # 伪指令扩展
        # 注意：参数解析需要增强，这里简化处理，依赖后续阶段的逗号清理
        if op == 'li':
            if len(tokens) < 3:
                raise ValueError(f"Error on line {line_number + 1}: 'li' instruction requires 2 arguments (rd, immediate). Got: '{instruction_part}'")
            rd = tokens[1].replace(',', '') # 移除寄存器名后的逗号
            try:
                imm = int(tokens[2], 0) # 自动检测立即数的进制 (e.g., 0x for hex)
            except ValueError:
                raise ValueError(f"Error on line {line_number + 1}: Invalid immediate value '{tokens[2]}' for 'li'.")

            # 假设 lui 的立即数是8位 (加载到高位), addi 的立即数是4位 (用于li的低位)
            # 基于之前代码的 li 展开逻辑
            upper_imm = (imm >> 4) & 0xFF
            lower_imm = imm & 0xF

            expanded_instructions.append(f'lui {rd}, 0x{upper_imm:X}')
            pc += 1
            # 只有当低4位非0时，或者整个数就是0-15（此时lui加载0，addi加载原数）才添加addi
            # 原来的逻辑是 `if lower_imm != 0:`
            # 如果 imm 本身就很小 (e.g., 0 to 15), upper_imm 会是0.
            # li rD, 5 -> lui rD, 0x0; addi rD, rD, 5
            # li rD, 0 -> lui rD, 0x0; (没有 addi)
            if lower_imm != 0 or (imm >=0 and imm <=0xF and upper_imm == 0) : # 确保小数值也能正确加载
                if imm == 0 and lower_imm == 0 and upper_imm == 0: # 特殊处理 li rD, 0，只用lui
                    pass
                else:
                    expanded_instructions.append(f'addi {rd}, {rd}, {lower_imm}')
                    pc += 1


        elif op == 'la': # la rd, label
            if len(tokens) < 3:
                raise ValueError(f"Error on line {line_number + 1}: 'la' instruction requires 2 arguments (rd, label). Got: '{instruction_part}'")
            rd = tokens[1].replace(',', '')
            label_ref = tokens[2]
            # 当前 'la' 仅扩展为一条 'lui' 指令。
            # 这意味着 'la' 加载的地址，其低位（如8位）必须为0，'lui' 的立即数是地址的高位部分。
            # 为了更通用的地址加载，'la' 通常会扩展为 'lui' 和 'addi'。
            # 这里我们保持原样，只生成 'lui'。
            expanded_instructions.append(f'lui {rd}, {label_ref}') # label_ref 会在 resolve_labels 中被替换
            pc += 1

        elif op == 'j': # j label
            if len(tokens) < 2:
                raise ValueError(f"Error on line {line_number + 1}: 'j' instruction requires 1 argument (label). Got: '{instruction_part}'")
            label_ref = tokens[1]
            expanded_instructions.append(f'jal r0, {label_ref}')
            pc += 1

        elif op == 'bge': # bge rs1, rs2, label
            if len(tokens) < 4:
                raise ValueError(f"Error on line {line_number + 1}: 'bge' instruction requires 3 arguments (rs1, rs2, label). Got: '{instruction_part}'")
            rs1 = tokens[1].replace(',', '')
            rs2 = tokens[2].replace(',', '')
            label_ref = tokens[3]
            expanded_instructions.append(f'ble {rs2}, {rs1}, {label_ref}') # 注意 rs1 和 rs2 的顺序为 ble 调换
            pc += 1

        else: # 其他标准指令
            expanded_instructions.append(instruction_part) # 添加原始（清理过的）指令部分
            pc += 1

    return expanded_instructions, label_map

# 修改后的标签解析函数
def resolve_labels(expanded_lines, label_map):
    resolved = []
    for idx, line in enumerate(expanded_lines):
        # 移除逗号并分割，与 assemble_line 的预处理方式保持一致
        # ( "imm(rs)" 格式中的括号也在这里被处理 )
        processed_line_for_tokens = line.replace(',', '').replace('(', ' ').replace(')', '')
        tokens = processed_line_for_tokens.split()

        if not tokens:
            continue

        instr = tokens[0]

        # --- 主要修改部分开始 ---
        if instr in ['ble', 'beq', 'jal']: # 对分支和跳转指令应用新的逻辑
            if len(tokens) < (3 if instr == 'jal' else 4):
                raise ValueError(f"Malformed branch/jump instruction: '{line}' at expanded index {idx}")

            last_arg = tokens[-1]
            try:
                int(last_arg, 0)
                resolved.append(line) # 如果已经是数字偏移，则直接使用
            except ValueError:
                # 是标签，需要解析
                label_name = last_arg
                if label_name not in label_map:
                    raise KeyError(f"Error: Undefined label '{label_name}' used in instruction: '{line}' at expanded index {idx}")

                # 原本的标签目标地址索引:
                # original_target_pc_index = label_map[label_name]

                # =========== 新增逻辑：根据您的要求调整目标地址 ===========
                # 您的期望是“跳转到inner loop所在行的下一条语句”。
                # 我们将此理解为：如果标签 L 指向指令 I，那么跳转实际目标是指令 I 之后的下一条指令。
                # 所以，我们将原始标签指向的地址索引 +1 作为新的目标地址索引。
                target_pc_index = label_map[label_name] + 1
                # =======================================================

                current_pc_index = idx
                # PC相对寻址偏移 = (新的目标地址索引) - 当前指令的地址索引 - 1
                offset = target_pc_index - current_pc_index - 1

                temp_tokens = tokens[:-1] + [str(offset)]
                resolved.append(' '.join(temp_tokens))
        # --- 主要修改部分结束 ---

        elif instr == 'lui':
            # lui rd, immediate_or_label
            if len(tokens) < 3:
                raise ValueError(f"Malformed LUI instruction: '{line}' at expanded index {idx}. Expected 'lui rd, immediate/label'")

            immediate_or_label_arg = tokens[2]
            if immediate_or_label_arg in label_map:
                # 如果 lui 的第二个参数是一个已定义的标签 (通常来自 'la' 伪指令)
                # 这里的逻辑是：label_map 中存储的值直接作为 lui 的立即数
                # CPU 执行 lui 时会将此立即数左移（如8位）
                # 例如：la a0, myData -> lui a0, myData_val_for_lui
                # 其中 myData_val_for_lui 是 label_map['myData'] 的值

                # 假设 label_map[label_name] 存储的是该标签对应的PC索引（或某种地址表示）
                # 对于 `la` 展开成的 `lui rd, label`, 这个 `label` 应该被替换成
                # 该标签地址的高位部分。
                # 如果 `la` 只生成 `lui`，那么 `lui` 加载的值（来自label_map）会被CPU左移。
                # 例如，如果 `mylabel` 在 `pc=20 (0x14)`，那么 `lui rd, mylabel` 会变成 `lui rd, 0x14`。
                # CPU 执行时 `rd = 0x14 << 8 = 0x1400`。
                # 这似乎是你原始代码对 `la` -> `lui` 转换的简化处理方式。

                label_value = label_map[immediate_or_label_arg]

                temp_tokens = list(tokens)
                # assemble_line 中的 lui 部分期望 tokens[2] 是一个十六进制字符串 "0xHH"
                temp_tokens[2] = f'0x{label_value:X}'
                resolved.append(' '.join(temp_tokens))
            else:
                # 如果不是标签，则假定它是普通的立即数（可能是 "0xHH" 或十进制数）
                # assemble_line 会处理它
                resolved.append(line)
        else:
            # 其他指令直接通过
            resolved.append(line)
    return resolved

# 指令汇编函数 (assemble_line)
def assemble_line(line):
    # 移除逗号，并将 "imm(rs)" 格式转换为空格分隔的 "imm rs"
    tokens = line.replace(',', '').replace('(', ' ').replace(')', '').split()
    instr = tokens[0]

    if instr == 'jal': # UJ-type: imm[11:0] rd opcode
        rd = reg_bin(tokens[1])
        imm_val = int(tokens[2], 0) # 支持各种进制的立即数
        imm = imm_bin(imm_val, 8) # 假设jal的立即数是8位 for this ISA
        # RISC-V JAL has a 20-bit imm. This is custom.
        # For your 16-bit format: imm(8) rd(4) opcode(4)
        # The format was imm + rd + opcode. Let's assume 8 bit imm.
        return imm + rd + opcode_map[instr] # Total 16 bits

    elif instr == 'jalr': # I-type like: imm[7:0] rs1 rd opcode
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2]) # rs1
        imm_val = int(tokens[3],0)
        imm = imm_bin(imm_val, 4) # 假设 JALR 的立即数是4位 for this ISA
        # Format: imm(4) rs1(4) rd(4) opcode(4)
        return imm + rs + rd + opcode_map[instr]

    elif instr in ['addi', 'subi']: # I-type: imm[3:0] rs1 rd opcode
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2]) # rs1
        imm_val = int(tokens[3],0)
        imm = imm_bin(imm_val, 4) # 立即数是4位
        return imm + rs + rd + opcode_map[instr]

    elif instr in ['beq', 'ble']: # SB-type variant: rs2 rs1 imm[3:0] opcode
        rs1 = reg_bin(tokens[1])
        rs2 = reg_bin(tokens[2])
        imm_val = int(tokens[3],0)
        imm = imm_bin(imm_val, 4) # 分支偏移是4位
        return rs2 + rs1 + imm + opcode_map[instr] # 顺序：rs2 rs1 imm op

    elif instr in ['lb', 'lw']: # I-type (Load): imm[3:0] rs1 rd opcode
        rd = reg_bin(tokens[1])
        imm_val = int(tokens[2],0) # offset
        rs = reg_bin(tokens[3])    # base register (rs1)
        imm = imm_bin(imm_val, 4)  # 偏移是4位
        return imm + rs + rd + opcode_map[instr]

    elif instr in ['sb', 'sw']: # S-type (Store): imm[3:0] rs1 rs2 opcode (rs2 is src reg)
        # Your format seems: imm rs rt opcode (rt is src)
        rt = reg_bin(tokens[1])   # Source register (rs2 in standard RISC-V)
        imm_val = int(tokens[2],0) # offset
        rs = reg_bin(tokens[3])   # Base register (rs1 in standard RISC-V)
        imm = imm_bin(imm_val, 4) # 偏移是4位
        return rt + rs + imm + opcode_map[instr] # 顺序 base_reg src_reg imm op

    elif instr in ['add', 'sub', 'and', 'or']: # R-type: rs2 rs1 rd opcode
        rd = reg_bin(tokens[1])
        rs1 = reg_bin(tokens[2])
        rs2 = reg_bin(tokens[3])
        return rs2 + rs1 + rd + opcode_map[instr] # 顺序：rs2 rs1 rd op

    elif instr == 'lui': # U-type: imm[7:0] rd opcode
        rd = reg_bin(tokens[1])
        # LUI的立即数应该是直接给定的，例如 "0xAB" 或 "171"
        imm_val = int(tokens[2], 0) # 支持各种进制
        if not (0 <= imm_val <= 0xFF): # LUI的立即数通常是无符号的，表示高位
            print(f"Warning: LUI immediate '{tokens[2]}' (value: {imm_val}) is outside the typical 8-bit unsigned range (0-255). It will be truncated/wrapped.")
        imm = format(imm_val & 0xFF, '08b') # 取低8位作为LUI的立即数
        return imm + rd + opcode_map[instr] # 顺序：imm rd op

    else:
        raise ValueError(f"Unknown instruction: {instr} in line '{line}'")


# 主汇编程序 (保持不变)
def assemble_program(lines):
    expanded, label_map = expand_pseudo_instructions(lines)

    # print("--- Expanded Instructions ---")
    # for i, l in enumerate(expanded):
    #     print(f"{i}: {l}")
    # print("--- Label Map ---")
    # for label, addr in label_map.items():
    #     print(f"{label}: {addr}")
    # print("---------------------------")

    resolved = resolve_labels(expanded, label_map)

    # print("--- Resolved Instructions ---")
    # for i, l in enumerate(resolved):
    #     print(f"{i}: {l}")
    # print("---------------------------")

    machine_code = []
    for line_num, line_content in enumerate(resolved):
        try:
            bin_code = assemble_line(line_content.strip())
            # 将16位二进制码格式化为 "XXXX_XXXX_XXXX_XXXX"
            formatted_bin_code = '_'.join([bin_code[i:i+4] for i in range(0, len(bin_code), 4)])
            machine_code.append(formatted_bin_code)
        except Exception as e:
            # 包含行号和内容的错误信息，便于调试
            print(f"Error assembling line #{line_num + 1} (resolved content: '{line_content.strip()}'): {e}")
            # 可以选择在这里 re-raise e 如果希望程序因错误停止
    return machine_code

# 主执行块 (保持不变)
if __name__ == '__main__':
    # 注意！！从 program.txt 文件读取汇编指令，若文件命名不同则及时更改
    try:
        with open('program.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: program.txt not found. Please ensure the file exists in the same directory.")
        exit(1)

    # 汇编生成机器码
    output = assemble_program(lines)

    # 打印机器码到终端
    print("\n机器码输出 ：")
    for line in output:
        print(line)

    # 输出机器码到文件 D:/learn/Git/testgit/test/test2.txt
    output_filename = 'D:/learn/Git/testgit/test/test2.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        for line in output:
            f.write(line + '\n')
    print(f"\nMachine code also written to {output_filename}")