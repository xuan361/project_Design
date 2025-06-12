# 若想切换 单独使用 或 配合 windows.py 使用 ，调整 expand_pseudo_instructions(lines) 末尾

import re

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
    #伪指令是li la j bge
}

# 寄存器映射
register_alias = {
    'r0': 0, 'ra': 1, 'sp': 2,
    **{f'a{i}': i + 3 for i in range(13)},
    # r0为恒0寄存器，r1为返回地址寄存器ra，r2为栈指针寄存器sp，其余为运算寄存器a0-a12(即r3-r15)
}

# 反向映射显示
reg_num_to_name = {v: k for k, v in register_alias.items()}
for i in range(16): # 确保所有 r0-r15 都有一个默认名称（如果不在alias中）
    if i not in reg_num_to_name:
        reg_num_to_name[i] = f'r{i}'


def reg_bin(reg_name):
    if reg_name in register_alias:
        reg_num = register_alias[reg_name]
    elif reg_name.startswith('r'):
        reg_num = int(reg_name[1:])
    else:
        raise ValueError(f"Unknown register name: {reg_name}")
    if not (0 <= reg_num <= 15):
        raise ValueError("Register out of bounds")
    return format(reg_num, '04b')

def imm_bin(val, bits=4):
    if not isinstance(val, int):
        val = int(str(val),0) # 允许十六进制字符串
    if val < 0:# 负立即数
        val = (1 << bits) + val
    return format(val % (1 << bits), f'0{bits}b')


def strip_comments(line):
    # 优先移除 // 和 # 类型的注释，然后是 \t 分割，最后去除首尾空格
    line_no_double_slash = line.split('//')[0]
    line_no_hash = line_no_double_slash.split('#')[0]

    line_no_tab_comment = line_no_hash.split('\t')[0] # 假设tab后的内容为注释或无关紧要
    return line_no_tab_comment.strip()


# 伪指令扩展函数
def expand_pseudo_instructions(lines):
    expanded_instructions = []    # 存储指令字串 (lui, addi, add 等)
    label_map = {}              # 存储指令标签的 "PC" (索引)
    current_expanded_instruction_pc = 0  # 指令的程序计数器

    data_lma_values = []        # 专门存储 _data_lma 的原始数值
    active_data_collection_label = None # 追踪当前是否在为 _data_lma 收集数据

    # 存储每条扩展后指令对应的原始源代码行号 (1-based)
    expanded_instr_source_lines = []

    for actual_source_line_number, raw_line in enumerate(lines, 1):
        line_for_label_detection = strip_comments(raw_line)

        if not line_for_label_detection:
            continue

        instruction_part = line_for_label_detection
        current_line_had_label = False

        if ':' in line_for_label_detection:
            label_name, rest_of_line = line_for_label_detection.split(':', 1)
            label_name = label_name.strip()
            current_line_had_label = True

            if not label_name:
                print(f"Warning on line {actual_source_line_number}: Empty label name. Processing rest: '{rest_of_line.strip()}'")
            elif ' ' in label_name or '\t' in label_name or ',' in label_name:
                print(f"Warning on line {actual_source_line_number}: Label '{label_name}' has space/comma.")

            if label_name:
                if label_name in label_map: # 检查是否与 data_lma_values 相关标签冲突 (如果有多个数据标签)
                    raise ValueError(f"Error on line {actual_source_line_number}: Duplicate label '{label_name}'")

                active_data_collection_label = label_name # 设置当前活动标签
                if label_name != '_data_lma': # 普通指令标签
                    label_map[label_name] = current_expanded_instruction_pc
                # 对于 _data_lma，不将其 pc 存入 label_map，因为它的数据单独处理

            instruction_part = rest_of_line.strip()

        # 如果这一行除了标签外没有其他内容，则跳过后续的指令/数据处理
        if not instruction_part:
            # 如果仅仅是 "_data_lma:" 这样的一行，active_data_collection_label 已被设置
            # 如果是 "other_label:"，active_data_collection_label 也被设置
            continue

        first_word = instruction_part.split(maxsplit=1)[0]

        # 检查是否为 _data_lma 活动标签下的 .byte 指令
        if active_data_collection_label == '_data_lma' and first_word == '.byte':
            try:
                args_content = instruction_part.split('.byte', 1)[1]
            except IndexError:
                raise ValueError(f"L{actual_source_line_number}: '.byte' for _data_lma needs args. Got: '{instruction_part}'")
            if not args_content.strip():
                raise ValueError(f"L{actual_source_line_number}: '.byte' for _data_lma needs args. Got: '{instruction_part}'")

            byte_values_str = args_content.strip().split(',')
            if not any(s.strip() for s in byte_values_str):
                raise ValueError(f"L{actual_source_line_number}: '.byte' for _data_lma no values: '{instruction_part}'")

            for val_str in byte_values_str:
                val_str = val_str.strip()
                if not val_str:
                    raise ValueError(f"L{actual_source_line_number}: Empty val in '.byte' for _data_lma: '{args_content}'")
                try:
                    byte_val = int(val_str, 0)
                except ValueError:
                    raise ValueError(f"L{actual_source_line_number}: Invalid num '{val_str}' in '.byte' for _data_lma.")
                if not (0 <= byte_val <= 127):
                    raise ValueError(f"L{actual_source_line_number}: Byte '{val_str}' out of 0-255 for _data_lma.")

                data_lma_values.append(byte_val) # 存储原始数值

            # 如果 _data_lma: 和 .byte 在同一行，或 .byte 是紧跟 _data_lma: 后的第一个有效部分，那么处理完这一行 .byte 后，认为 _data_lma 的数据定义結束
            # 如果一个标签不是 _data_lma，或者指令不是 .byte，则 active_data_collection_label 会在下一轮循环开始时被新的标签覆盖，或者如果下一行没有标签，它将保持
            # 为了避免非 _data_lma 标签后的 .byte 被错误收集，或 _data_lma 后的非 .byte 行被忽略，在处理完 _data_lma 的 .byte 后，或遇到非 _data_lma 标签的指令行时，可以重置它
            # 遇到任何常规指令处理时，清除 active_data_collection_label (如果它是_data_lma)
            if not current_line_had_label: # 如果 .byte 指令独占一行，在其标签之后
                active_data_collection_label = None # 清除状态，避免干扰下一行

            continue
        # 应该用不上了
        # 处理不属于 _data_lma 的 .byte 指令 (如果有的话，按老方式或报错)
        # elif first_word == '.byte':
        #     # 按老方式处理，將 "00000000XXXXXXXX" 加入 expanded_instructions
        #     # 同时 pc 也需要增加
        #     active_data_collection_label = None # 清除非 _data_lma 标签的影响

        else:
            # 处理所有常规指令和伪指令
            if active_data_collection_label == '_data_lma': # 如果之前是_data_lma，但现在不是.byte了
                active_data_collection_label = None # 重置状态

            tokens = instruction_part.split()
            if not tokens:
                # 这一行在标签后可能是空的，或者 strip 后
                continue

            op = tokens[0]

            if op == 'li':
                if len(tokens) < 3:
                    raise ValueError(f"Error on line {actual_source_line_number}: 'li' requires 2 args. Got: '{instruction_part}'")
                rd = tokens[1].replace(',', '')
                try:
                    imm = int(tokens[2], 0) # 解析立即数
                except ValueError:
                    raise ValueError(f"Error on line {actual_source_line_number}: Invalid immediate for 'li'.")

                # 16位 (超出部分会被截断或按 Python 整数处理)
                target_val = imm & 0xFFFF

                # lui 负责处理前8位 (imm[15:8])
                upper_8_bits = (target_val >> 8) & 0xFF
                expanded_instructions.append(f'lui {rd}, 0x{upper_8_bits:X}')
                expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                current_expanded_instruction_pc += 1

                #    addi 负责处理后8位 (imm[7:0])，可能需要两条 addi 指令
                #       0010_0001_0011_1100
                #       //imm   rs,  rd,  addi    (r3) = (r1) + 2     // 此时(r3) = 4, pc = 6
                #    每条 addi 只能处理4位的立即数
                #    rd 的当前值是 (upper_8_bits << 8)
                #    需要 imm[7:0] 加到 rd 上。
                #    imm[7:0] = (imm[7:4] << 4) + imm[3:0]
                #    但 addi 是直接相加，所以直接加 imm[7:4] 的值和 imm[3:0] 的值。

                middle_4_bits_value = (target_val >> 4) & 0xF  #  imm[7:4]
                lower_4_bits_value = target_val & 0xF          #  imm[3:0]

                # 只有当整个立即数不为0时，才考虑添加 addi
                # （如果 imm 为0, `lui rd, 0x0` 足够）
                if target_val != 0:
                    # 如果中间4位 (imm[7:4]) 非零，则添加第一条 addi
                    if middle_4_bits_value != 0:
                        expanded_instructions.append(f'addi {rd}, {rd}, {middle_4_bits_value}')
                        expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                        current_expanded_instruction_pc += 1
                    # 如果最低4位 (imm[3:0]) 非零，则添加第二个 addi
                    # 或者，如果高12位都是0 (即 upper_8_bits 和 middle_4_bits_value 都是0)，
                    # 且这个最低4位本身就是整个数（例如 li rd, 5），那么也需要这个addi

                    if lower_4_bits_value != 0:
                        expanded_instructions.append(f'addi {rd}, {rd}, {lower_4_bits_value}')
                        expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                        current_expanded_instruction_pc += 1
                    # 如果一个数是例如 0x0M0 (M非0)，例如 0x020，即0x0020
                    # lui rd, 0x0
                    # addi rd, rd, 2 (middle_4_bits_value)
                    # lower_4_bits_value 为0，不用第二个 addi

            elif op == 'la':
                if len(tokens) < 3: raise ValueError(f"L{actual_source_line_number}: la needs 2 args.")
                rd = tokens[1].replace(',', '')
                label_ref = tokens[2]
                expanded_instructions.append(f'lui {rd}, {label_ref}')
                expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                current_expanded_instruction_pc += 1

            elif op == 'j':
                if len(tokens) < 2: raise ValueError(f"L{actual_source_line_number}: j needs 1 arg.")
                label_ref = tokens[1]
                expanded_instructions.append(f'jal r0, {label_ref}')
                expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                current_expanded_instruction_pc += 1

            elif op == 'jal' and len(tokens) == 2: # 伪指令 jal (跳转，返回地址到r0)
                label_ref = tokens[1].replace(',', '')
                expanded_instructions.append(f'jal r0, {label_ref}')
                expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                current_expanded_instruction_pc += 1

            elif op == 'bge':
                if len(tokens) < 4: raise ValueError(f"L{actual_source_line_number}: bge needs 3 args.")
                rs1 = tokens[1].replace(',', ''); rs2 = tokens[2].replace(',', ''); label_ref = tokens[3]
                expanded_instructions.append(f'ble {rs2}, {rs1}, {label_ref}')
                expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                current_expanded_instruction_pc += 1
                
            else: # 其他真实指令 (非伪指令，非.byte)
                expanded_instructions.append(instruction_part)
                expanded_instr_source_lines.append(actual_source_line_number) # 记录行号
                current_expanded_instruction_pc += 1

    """
    开头提到的二选一
    """
    # # 1.单独使用
    # return expanded_instructions, label_map, data_lma_values

    # 2.配合 windows.py 使用
    return expanded_instructions, label_map, data_lma_values, expanded_instr_source_lines

# 标签解析函数
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

        if instr in ['ble', 'beq', 'jal']:
            if len(tokens) < (3 if instr == 'jal' else 4):
                raise ValueError(f"Malformed branch/jump instruction: '{line}' at expanded index {idx}")

            last_arg = tokens[-1]
            try:
                int(last_arg, 0)
                resolved.append(line) # 如果已经偏移，则直接使用
            except ValueError:
                # 是标签，需要解析
                label_name = last_arg
                if label_name not in label_map:
                    raise KeyError(f"Error: Undefined label '{label_name}' used in instruction: '{line}' at expanded index {idx}")
                #如果标签 L 指向指令 I，那么跳转实际目标是指令 I 之后的下一条指令。
                target_pc_index = label_map[label_name] + 1  #加1

                current_pc_index = idx
                # PC相对寻址偏移 = (新的目标地址索引) - 当前指令的地址索引 - 1
                offset = target_pc_index - current_pc_index - 1

                temp_tokens = tokens[:-1] + [str(offset)]
                resolved.append(' '.join(temp_tokens))


        elif instr == 'lui':
            # lui rd, immediate_or_label
            if len(tokens) < 3:
                raise ValueError(f"Malformed LUI instruction: '{line}' at expanded index {idx}. Expected 'lui rd, immediate/label'")

            immediate_or_label_arg = tokens[2]
            if immediate_or_label_arg in label_map:
                # 如果 lui 的第二个参数是一个已定义的标签 (通常来自 'la' 伪指令)
                # 逻辑：label_map 中存储的值直接作为 lui 的立即数，CPU 执行 lui 时会将此立即数左移（如8位）
                # 例：la a0, myData -> lui a0, myData_val_for_lui
                # 其中 myData_val_for_lui 是 label_map['myData'] 的值

                # 假设 label_map[label_name] 存储的是该标签对应的PC索引（或某种地址表示）
                # 对于 `la` 展开成的 `lui rd, label`, 这个 `label` 应该被替换成该标签地址的高位部分。
                # 如果 `la` 只生成 `lui`，那么 `lui` 加载的值（来自label_map）会被CPU左移。
                # 若 `mylabel` 在 `pc=20 (0x14)`，那么 `lui rd, mylabel` 会变成 `lui rd, 0x14`。
                # CPU 执行时 `rd = 0x14 << 8 = 0x1400`

                label_value = label_map[immediate_or_label_arg]

                temp_tokens = list(tokens)
                # assemble_line 中的 lui 部分期望 tokens[2] 是一个十六进制字符串 "0xHH"
                temp_tokens[2] = f'0x{label_value:X}'
                resolved.append(' '.join(temp_tokens))
            else:
                # 如果不是标签，则假定它是普通的立即数（可能是 "0xHH" 或十进制数），让assemble_line 处理
                resolved.append(line)
        else:
            # 其他指令直接通过
            resolved.append(line)
    return resolved

# 指令汇编函数
def assemble_line(line):

    stripped_line = line.strip()
    # 检查这行是否已经是16位的二进制字符串 (由 .byte 生成)
    if re.fullmatch(r'[01]{16}', stripped_line):
        return stripped_line # 如果是，直接返回

    # 移除逗号，并将 "imm(rs)" 格式转换为空格分隔的 "imm rs"
    tokens = line.replace(',', '').replace('(', ' ').replace(')', '').split()
    instr = tokens[0]

    if instr == 'jal': # UJ-type: imm[11:0] rd opcode
        rd = reg_bin(tokens[1])
        imm_val = int(tokens[2], 0) # 支持各种进制的立即数
        imm = imm_bin(imm_val, 8) # jal的立即数是8位
        # format: imm(8) rd(4) opcode(4)
        return imm + rd + opcode_map[instr]

    elif instr == 'jalr': # I-type like: imm[7:0] rs1 rd opcode
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2]) # rs1
        imm_val = int(tokens[3],0)
        imm = imm_bin(imm_val, 4)
        # imm(4) rs1(4) rd(4) opcode(4)
        return imm + rs + rd + opcode_map[instr]

    elif instr in ['addi', 'subi']: # I-type: imm[3:0] rs1 rd opcode
        rd = reg_bin(tokens[1])
        rs = reg_bin(tokens[2]) # rs1
        imm_val = int(tokens[3],0)
        imm = imm_bin(imm_val, 4)
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

    elif instr in ['sb', 'sw']: # S-type (Store): imm[3:0] rs1 rs2 opcode （rs2 是源寄存器）
        # format: imm rs rt opcode (rt is src)
        rt = reg_bin(tokens[1])   # Source register
        imm_val = int(tokens[2],0) # offset
        rs = reg_bin(tokens[3])   # 基址寄存器
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
        imm = format(imm_val & 0xFF, '08b') # 取低8位作为lui的立即数
        return imm + rd + opcode_map[instr] # 顺序：imm rd op

    else:
        raise ValueError(f"Unknown instruction: {instr} in line '{line}'")


# 主汇编程序
def assemble_program(lines):
    expanded, label_map = expand_pseudo_instructions(lines)
    # 调试部分，应该用不上了
    # print("--- Expanded Instructions ---")
    # for i, l in enumerate(expanded):
    #     print(f"{i}: {l}")
    # print("--- Label Map ---")
    # for label, addr in label_map.items():
    #     print(f"{label}: {addr}")
    # print("---------------------------")

    resolved = resolve_labels(expanded, label_map)
    # 调试部分，应该用不上了
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

    return machine_code

def write_machine_code_to_file(final_output_lines, output_filename="machine_code_output.txt"):
    # 将格式化后的机器码列表写入到指定文件中

    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            for line in final_output_lines:
                f.write(line + '\n')
        print(f"机器码已成功写入到 {output_filename}")
    except IOError as e:
        print(f"错误：无法写入文件 {output_filename}: {e}")


# 主执行块
if __name__ == '__main__':
    """
    注意！！从 program.txt 文件读取汇编指令，若文件命名不同则及时更改
    """
    
    try:
        with open('program2.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print("Error: program.txt not found. Please ensure the file exists in the same directory.")
        exit(1)

    expanded_instr_strings, label_map, data_lma_numeric_values = expand_pseudo_instructions(lines)

    # 解析指令中的标签
    resolved_instr_strings = resolve_labels(expanded_instr_strings, label_map)

    instruction_machine_code_raw = [] # 存储纯16位二进制指令
    # 调试部分，应该用不上了
    #print("\n--- Assembling Instructions ---") #
    for i, line_content in enumerate(resolved_instr_strings):
        try:
            # 调试部分，应该用不上了
            # print(f"Assembling instruction line {i}: {line_content.strip()}")
            bin_code = assemble_line(line_content.strip()) # assemble_line 返回 "XXXXXXXXXXXXXXXX"
            instruction_machine_code_raw.append(bin_code)
        except Exception as e:
            print(f"Error assembling instruction line #{i + 1} (resolved: '{line_content.strip()}'): {e}")
            # exit(1) # 发生错误时可以选择退出

    # 4.  ROM 输出部分 (前128行)
    rom_output_lines = []
    for i in range(len(instruction_machine_code_raw)):
        if i < 128: # 最多取128条指令放入ROM
            formatted_bin_code = '_'.join([instruction_machine_code_raw[i][j:j+4] for j in range(0, 16, 4)])
            rom_output_lines.append(formatted_bin_code)

    # 如果指令不足128行，用0填充
    while len(rom_output_lines) < 128:
        rom_output_lines.append("0000_0000_0000_0000")

    if len(instruction_machine_code_raw) > 128:
        print(f"Warning: {len(instruction_machine_code_raw)} instructions generated, but ROM section is limited to 128 lines. Truncating.")

    # 5.  Data (_data_lma) 输出部分 (从第257行开始)
    data_output_lines = []
    # 调试部分，应该用不上了
    #print(f"\n--- Formatting _data_lma ({len(data_lma_numeric_values)} bytes) ---")
    i = 0
    while i < len(data_lma_numeric_values):
        byte1_val = data_lma_numeric_values[i]
        byte1_bin = format(byte1_val, '08b')
        byte1_formatted = f"{byte1_bin[0:4]}_{byte1_bin[4:8]}" # "XXXX_XXXX"

        if i + 1 < len(data_lma_numeric_values): # 如果还有下一个数配对
            byte2_val = data_lma_numeric_values[i+1]
            byte2_bin = format(byte2_val, '08b')
            byte2_formatted = f"{byte2_bin[0:4]}_{byte2_bin[4:8]}" # "YYYY_YYYY"
        else: # 奇数个数字，最后一个后面全填0
            byte2_formatted = "0000_0000"

        data_output_lines.append(f"{byte1_formatted}_{byte2_formatted}")
        i += 2

    final_output_lines = rom_output_lines + data_output_lines

    # 打印机器码到终端
    #print("\n机器码输出 ：")
    for line in final_output_lines:
        print(line)

    # 输出机器码到文件 machine_code_output.txt
    write_machine_code_to_file(final_output_lines, "machine_code_output_standalone.txt")
    # 调试部分，应该用不上了
    #print(f"\nMachine code also written to {output_filename}")