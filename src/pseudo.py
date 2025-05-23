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
    #伪指令是li la j bge
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

    line_no_tab_comment = line_no_hash.split('\t')[0] # 假设tab后的内容为注释或无关紧要
    return line_no_tab_comment.strip()


# 伪指令扩展函数
def expand_pseudo_instructions(lines):
    expanded_instructions = []    # 存儲指令字串 (lui, addi, add 等)
    label_map = {}              # 存儲指令標籤的 "PC" (索引)
    pc = 0                      # 指令的程序計數器

    data_lma_values = []        # 專門存儲 _data_lma 的原始數值
    active_data_collection_label = None # 用於追蹤當前是否在為 _data_lma 收集數據

    for line_number, raw_line in enumerate(lines):
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
                print(f"Warning on line {line_number + 1}: Empty label name. Processing rest: '{rest_of_line.strip()}'")
            elif ' ' in label_name or '\t' in label_name or ',' in label_name:
                print(f"Warning on line {line_number + 1}: Label '{label_name}' has space/comma.")

            if label_name:
                if label_name in label_map: # 檢查是否与 data_lma_values 相關標籤衝突 (如果有多個數據標籤)
                    raise ValueError(f"Error on line {line_number + 1}: Duplicate label '{label_name}'")

                active_data_collection_label = label_name # 設置當前活動標籤
                if label_name != '_data_lma': # 普通指令標籤
                    label_map[label_name] = pc
                # 对于 _data_lma，不將其 pc 存入 label_map，因為它的数据单独处理

            instruction_part = rest_of_line.strip()

        # 如果這一行除了標籤外沒有其他內容，則跳过后續的指令/數據處理
        if not instruction_part:
            # 如果仅仅是 "_data_lma:" 这样的一行，active_data_collection_label 已被設置
            # 如果是 "other_label:"，active_data_collection_label 也被設置
            continue

        first_word = instruction_part.split(maxsplit=1)[0]

        # 檢查是否為 _data_lma 活動標籤下的 .byte 指令
        if active_data_collection_label == '_data_lma' and first_word == '.byte':
            try:
                args_content = instruction_part.split('.byte', 1)[1]
            except IndexError:
                raise ValueError(f"L{line_number + 1}: '.byte' for _data_lma needs args. Got: '{instruction_part}'")
            if not args_content.strip():
                raise ValueError(f"L{line_number + 1}: '.byte' for _data_lma needs args. Got: '{instruction_part}'")

            byte_values_str = args_content.strip().split(',')
            if not any(s.strip() for s in byte_values_str):
                raise ValueError(f"L{line_number + 1}: '.byte' for _data_lma no values: '{instruction_part}'")

            for val_str in byte_values_str:
                val_str = val_str.strip()
                if not val_str:
                    raise ValueError(f"L{line_number + 1}: Empty val in '.byte' for _data_lma: '{args_content}'")
                try:
                    byte_val = int(val_str, 0)
                except ValueError:
                    raise ValueError(f"L{line_number + 1}: Invalid num '{val_str}' in '.byte' for _data_lma.")
                if not (0 <= byte_val <= 255):
                    raise ValueError(f"L{line_number + 1}: Byte '{val_str}' out of 0-255 for _data_lma.")

                data_lma_values.append(byte_val) # 存儲原始數值

            # 如果 _data_lma: 和 .byte 在同一行，或 .byte 是緊跟 _data_lma: 後的第一個有效部分，那麼處理完這一行 .byte 後，我們認為 _data_lma 的數據定義結束了（簡化處理）。
            # 如果一個標籤不是 _data_lma，或者指令不是 .byte，則 active_data_collection_label 會在下一輪循環開始時被新的標籤覆蓋，或者如果下一行沒有標籤，它會保持。
            # 為了避免非 _data_lma 標籤後的 .byte 被錯誤收集，或 _data_lma 後的非 .byte 行被忽略，在處理完 _data_lma 的 .byte 后，或遇到非 _data_lma 標籤的指令行時，可以重置它。
            # 此處簡化：假設 _data_lma 的 .byte 要么同在一行，要么紧跟其后。
            # 遇到任何常規指令處理時，應清除 active_data_collection_label (如果它是_data_lma)。
            if not current_line_had_label: # 如果 .byte 指令獨占一行，在其標籤之後
                active_data_collection_label = None # 清除狀態，避免影響下一行

        # 处理不属于 _data_lma 的 .byte 指令 (如果有的話，按舊方式或報錯)
        # elif first_word == '.byte':
        #     # ... 按舊方式處理，將 "00000000XXXXXXXX" 加入 expanded_instructions ...
        #     # 同時 pc 也需要增加
        #     active_data_collection_label = None # 清除非 _data_lma 標籤的影響

        else:
            # 處理所有常規指令和偽指令 (li, la, j, add 等)
            if active_data_collection_label == '_data_lma': # 如果之前是_data_lma，但現在不是.byte了
                active_data_collection_label = None # 重置狀態

            tokens = instruction_part.split()
            if not tokens:
                # 這一行在標籤後可能是空的，或者 strip 後變空
                # `if not instruction_part: continue` 應該已經處理了這種情況
                continue

            op = tokens[0]

            if op == 'li':
                if len(tokens) < 3: raise ValueError(f"L{line_number+1}: li needs 2 args.")
                rd = tokens[1].replace(',', '')
                try: imm = int(tokens[2], 0)
                except ValueError: raise ValueError(f"L{line_number+1}: Invalid imm for li: {tokens[2]}")
                upper_imm = (imm >> 4) & 0xFF
                lower_imm = imm & 0xF
                expanded_instructions.append(f'lui {rd}, 0x{upper_imm:X}')
                pc += 1
                if lower_imm != 0 or (imm >=0 and imm <=0xF and upper_imm == 0) :
                    if not (imm == 0 and lower_imm == 0 and upper_imm == 0):
                        expanded_instructions.append(f'addi {rd}, {rd}, {lower_imm}')
                        pc += 1

            elif op == 'la':
                if len(tokens) < 3: raise ValueError(f"L{line_number+1}: la needs 2 args.")
                rd = tokens[1].replace(',', '')
                label_ref = tokens[2]
                expanded_instructions.append(f'lui {rd}, {label_ref}')
                pc += 1

            elif op == 'j':
                if len(tokens) < 2: raise ValueError(f"L{line_number+1}: j needs 1 arg.")
                label_ref = tokens[1]
                expanded_instructions.append(f'jal r0, {label_ref}')
                pc += 1

            elif op == 'jal' and len(tokens) == 2:
                label_ref = tokens[1].replace(',', '')
                expanded_instructions.append(f'jal r0, {label_ref}')
                pc += 1

            elif op == 'bge':
                if len(tokens) < 4: raise ValueError(f"L{line_number+1}: bge needs 3 args.")
                rs1 = tokens[1].replace(',', ''); rs2 = tokens[2].replace(',', ''); label_ref = tokens[3]
                expanded_instructions.append(f'ble {rs2}, {rs1}, {label_ref}')
                pc += 1
                
            else: # 其他指令
                expanded_instructions.append(instruction_part)
                pc += 1

    return expanded_instructions, label_map, data_lma_values

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

        if instr in ['ble', 'beq', 'jal']:
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
                # 这里的逻辑是：label_map 中存储的值直接作为 lui 的立即数，CPU 执行 lui 时会将此立即数左移（如8位）
                # 例如：la a0, myData -> lui a0, myData_val_for_lui
                # 其中 myData_val_for_lui 是 label_map['myData'] 的值

                # 假设 label_map[label_name] 存储的是该标签对应的PC索引（或某种地址表示）
                # 对于 `la` 展开成的 `lui rd, label`, 这个 `label` 应该被替换成该标签地址的高位部分。
                # 如果 `la` 只生成 `lui`，那么 `lui` 加载的值（来自label_map）会被CPU左移。
                # 例如，如果 `mylabel` 在 `pc=20 (0x14)`，那么 `lui rd, mylabel` 会变成 `lui rd, 0x14`。
                # CPU 执行时 `rd = 0x14 << 8 = 0x1400`

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

    expanded_instr_strings, label_map, data_lma_numeric_values = expand_pseudo_instructions(lines)

    # 解析指令中的标签
    resolved_instr_strings = resolve_labels(expanded_instr_strings, label_map)

    instruction_machine_code_raw = [] # 存儲純16位二進位指令 (無底線)
    #print("\n--- Assembling Instructions ---") # 調試信息
    for i, line_content in enumerate(resolved_instr_strings):
        try:
            # print(f"Assembling instruction line {i}: {line_content.strip()}") # 調試
            bin_code = assemble_line(line_content.strip()) # assemble_line 返回 "XXXXXXXXXXXXXXXX"
            instruction_machine_code_raw.append(bin_code)
        except Exception as e:
            print(f"Error assembling instruction line #{i + 1} (resolved: '{line_content.strip()}'): {e}")
            # exit(1) # 发生错误时可以选择退出

    # 4.  ROM 輸出部分 (前256行)
    rom_output_lines = []
    for i in range(len(instruction_machine_code_raw)):
        if i < 256: # 最多取256條指令放入ROM
            formatted_bin_code = '_'.join([instruction_machine_code_raw[i][j:j+4] for j in range(0, 16, 4)])
            rom_output_lines.append(formatted_bin_code)

    # 如果指令不足256行，用0填充
    while len(rom_output_lines) < 256:
        rom_output_lines.append("0000_0000_0000_0000")

    if len(instruction_machine_code_raw) > 256:
        print(f"Warning: {len(instruction_machine_code_raw)} instructions generated, but ROM section is limited to 256 lines. Truncating.")

    # 5.  Data (_data_lma) 输出部分 (从第257行开始)
    data_output_lines = []
    #print(f"\n--- Formatting _data_lma ({len(data_lma_numeric_values)} bytes) ---") # 調試信息
    i = 0
    while i < len(data_lma_numeric_values):
        byte1_val = data_lma_numeric_values[i]
        byte1_bin = format(byte1_val, '08b')
        byte1_formatted = f"{byte1_bin[0:4]}_{byte1_bin[4:8]}" # "XXXX_XXXX"

        if i + 1 < len(data_lma_numeric_values): # 如果還有下一個位元組配對
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
    output_filename = 'machine_code_output.txt'
    with open(output_filename, 'w', encoding='utf-8') as f:
        for line in final_output_lines:
            f.write(line + '\n')
    #print(f"\nMachine code also written to {output_filename}")