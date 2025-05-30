import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import re

# parts of source code
# opcode_map  register_alias  reg_bin(reg_name)  imm_bin(val, bits=4)  strip_comments(line)  expand_pseudo_instructions(lines)  resolve_labels(expanded_lines, label_map)  assemble_line(line)

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

# (新建) 如果需要，可以进行反向映射显示
reg_num_to_name = {v: k for k, v in register_alias.items()}
for i in range(16): # 确保所有 r0-r15 都有一个默认名称（如果不在alias中）
    if i not in reg_num_to_name:
        reg_num_to_name[i] = f'r{i}'


def reg_bin(reg_name):
    if reg_name in register_alias:
        reg_num = register_alias[reg_name]
    elif reg_name.startswith('r') and reg_name[1:].isdigit():
        reg_num = int(reg_name[1:])
    else:
        raise ValueError(f"Unknown register name: {reg_name}")
    if not (0 <= reg_num <= 15):
        raise ValueError(f"Register number {reg_num} out of range (0-15)")
    return format(reg_num, '04b')

def imm_bin(val, bits=4):
    if not isinstance(val, int):
        val = int(str(val),0) # Allow hex strings like "0x..."
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
    expanded_instructions = []    # 存儲指令字串 (lui, addi, add 等)
    label_map = {}              # 存储指令标签的 "PC" (索引)
    pc = 0                      # 指令的程序计数器

    data_lma_values = []        # 专门存储 _data_lma 的原始數值
    active_data_collection_label = None # 用于追踪当前是否在为 _data_lma 收集数据

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
                if label_name in label_map: # 检查是否与 data_lma_values 相关标签冲突 (如果有多个数据标签)
                    raise ValueError(f"Error on line {line_number + 1}: Duplicate label '{label_name}'")

                active_data_collection_label = label_name # 设置当前活动标签
                if label_name != '_data_lma': # 普通指令标签
                    label_map[label_name] = pc
                # 对于 _data_lma，不将其 pc 存入 label_map，因为它的数据单独处理

            instruction_part = rest_of_line.strip()

        # 如果这一行除了标签外没有其他內容，则跳过后续的指令/数据处理
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

                data_lma_values.append(byte_val) # 存储原始数值

            # 如果 _data_lma: 和 .byte 在同一行，或 .byte 是紧跟 _data_lma: 后的第一个有效部分，那么处理完这一行 .byte 后，认为 _data_lma 的数据定义結束
            # 如果一个标签不是 _data_lma，或者指令不是 .byte，则 active_data_collection_label 会在下一轮循环开始时被新的标签覆盖，或者如果下一行没有标签，它将保持
            # 为了避免非 _data_lma 标签后的 .byte 被错误收集，或 _data_lma 后的非 .byte 行被忽略，在处理完 _data_lma 的 .byte 后，或遇到非 _data_lma 标签的指令行时，可以重置它
            # 遇到任何常规指令处理时，清除 active_data_collection_label (如果它是_data_lma)
            if not current_line_had_label: # 如果 .byte 指令独占一行，在其标签之后
                active_data_collection_label = None # 清除状态，避免干扰下一行

        # 应该用不上
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
                    raise ValueError(f"Error on line {line_number + 1}: 'li' instruction requires 2 arguments (rd, immediate). Got: '{instruction_part}'")
                rd = tokens[1].replace(',', '')
                try:
                    imm = int(tokens[2], 0) # 解析立即数
                except ValueError:
                    raise ValueError(f"Error on line {line_number + 1}: Invalid immediate value '{tokens[2]}' for 'li'.")

                # 16位 (超出部分会被截断或按 Python 整数处理)
                target_val = imm & 0xFFFF

                # lui 负责处理前8位 (imm[15:8])
                upper_8_bits = (target_val >> 8) & 0xFF
                expanded_instructions.append(f'lui {rd}, 0x{upper_8_bits:X}')
                pc += 1

                #    addi 负责处理后8位 (imm[7:0])，可能需要两条 addi 指令
                #    因为根据
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
                        pc += 1
                    # 如果最低4位 (imm[3:0]) 非零，则添加第二个 addi
                    # 或者，如果高12位都是0 (即 upper_8_bits 和 middle_4_bits_value 都是0)，
                    # 且这个最低4位本身就是整个数（例如 li rd, 5），那么也需要这个addi

                    if lower_4_bits_value != 0:
                        expanded_instructions.append(f'addi {rd}, {rd}, {lower_4_bits_value}')
                        pc += 1
                    # 如果一个数是例如 0x0M0 (M非0)，例如 0x020，即0x0020
                    # lui rd, 0x0
                    # addi rd, rd, 2 (middle_4_bits_value)
                    # lower_4_bits_value 为0，不用第二个 addi

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
        # 16-bit format: imm(8) rd(4) opcode(4)
        return imm + rd + opcode_map[instr] # Total 16 bits

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
        imm = format(imm_val & 0xFF, '08b') # 取低8位作为lui的立即数
        return imm + rd + opcode_map[instr] # 顺序：imm rd op

    else:
        raise ValueError(f"Unknown instruction: {instr} in line '{line}'")
# --- End of source code ---

class Simulator16Bit:
    def __init__(self):
        self.registers = [0] * 16  # r0 to r15
        self.memory = ["0000_0000_0000_0000"] * 512 # Memory for 512 words (16-bit each)
        self.pc = 0
        self.halted = False
        self.machine_code = [] # To store assembled code before loading to memory
        self.label_map = {}

        # Initialize r0 to 0, though it should be enforced by instruction execution
        self.registers[register_alias['r0']] = 0

    def reset(self):
        self.registers = [0] * 16
        self.pc = 0
        self.halted = False
        # self.memory can be cleared or reloaded from self.machine_code
        self.load_machine_code_to_memory() # Reload current machine code
        print("Simulator Reset.")
        self.print_regs()

    def get_reg_value(self, reg_idx):
        if not (0 <= reg_idx <= 15):
            raise ValueError(f"Invalid register index: {reg_idx}")
        if reg_idx == register_alias['r0']: # Ensure r0 is always 0
            return 0
        return self.registers[reg_idx]

    def set_reg_value(self, reg_idx, value):
        if not (0 <= reg_idx <= 15):
            raise ValueError(f"Invalid register index: {reg_idx}")
        if reg_idx != register_alias['r0']: # r0 cannot be changed
            # Values are 16-bit, so simulate overflow/wrapping if necessary
            self.registers[reg_idx] = value & 0xFFFF # Ensure 16-bit value
        else:
            self.registers[reg_idx] = 0 # r0 is always 0

    def load_program_from_source(self, asm_lines):
        """
Uses the user's assembler logic to convert assembly lines to machine code
and stores it internally.
        """
        try:
            # 1. Expand Pseudo Instructions (using user's function)
            expanded_instr, self.label_map, data_lma_values = expand_pseudo_instructions(asm_lines)
            # print(f"Expanded: {expanded_instr}")
            # print(f"Labels: {self.label_map}")
            # print(f"DataLMA: {data_lma_values}")


            # 2. Resolve Labels (using user's function)
            resolved_instr = resolve_labels(expanded_instr, self.label_map)
            # print(f"Resolved: {resolved_instr}")

            # 3. Assemble each resolved instruction line (using user's function)
            raw_machine_code = []
            for line_content in resolved_instr:
                if line_content.strip(): # Ensure not empty
                    bin_code = assemble_line(line_content.strip()) # Returns "XXXXXXXXXXXXXXXX"
                    raw_machine_code.append(bin_code)
            # print(f"Raw MC: {raw_machine_code}")

            # 4. Handle _data_lma values and combine with instruction code
            # Your assembler produces flat `final_output_lines` with instructions then data,
            # padded to 256 lines for instructions.
            # This simplified loader will just use raw_machine_code for now.
            # We need to align this with how your assembler structures final output.

            self.machine_code = []
            # Format and store instruction machine code
            for i, code in enumerate(raw_machine_code):
                if i < 256: # Max 256 instructions
                    self.machine_code.append('_'.join([code[j:j+4] for j in range(0, 16, 4)]))

            # Pad with zeros if less than 256 instructions
            while len(self.machine_code) < 256:
                self.machine_code.append("0000_0000_0000_0000")

            # Add data_lma values
            # This part needs to correctly use `data_lma_numeric_values`
            # For now, we'll assume the assembler output format used by `load_machine_code_to_memory`

            # For simplicity here, let's assume machine_code is just the raw_machine_code output for instructions
            # and data part needs more careful integration from your main script's logic.
            temp_formatted_code = []
            for code in raw_machine_code:
                temp_formatted_code.append('_'.join([code[j:j+4] for j in range(0, 16, 4)]))

            # Let's refine this to more closely match your assembler output structure
            instruction_machine_code_formatted = []
            for code in raw_machine_code: # Assuming raw_machine_code is only from instructions for now
                instruction_machine_code_formatted.append('_'.join([code[j:j+4] for j in range(0, 16, 4)]))

            rom_output_lines = instruction_machine_code_formatted[:256]
            while len(rom_output_lines) < 256:
                rom_output_lines.append("0000_0000_0000_0000")

            data_output_lines = []
            k = 0
            while k < len(data_lma_values):
                byte1_val = data_lma_values[k]
                byte1_bin = format(byte1_val, '08b')
                byte1_formatted = f"{byte1_bin[0:4]}_{byte1_bin[4:8]}"
                if k + 1 < len(data_lma_values):
                    byte2_val = data_lma_values[k+1]
                    byte2_bin = format(byte2_val, '08b')
                    byte2_formatted = f"{byte2_bin[0:4]}_{byte2_bin[4:8]}"
                else:
                    byte2_formatted = "0000_0000"
                data_output_lines.append(f"{byte1_formatted}_{byte2_formatted}")
                k += 2

            self.machine_code = rom_output_lines + data_output_lines
            # print(f"Final MC for simulator: {self.machine_code[:5]} ...")


            self.load_machine_code_to_memory()
            self.pc = 0
            self.halted = False
            return True, "Assembled successfully."
        except Exception as e:
            self.machine_code = []
            print(f"Assembly Error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Assembly Error: {e}"

    def load_machine_code_to_memory(self):
        self.memory = ["0000_0000_0000_0000"] * len(self.memory) # Clear memory first
        # Load the assembled program into memory
        for i, code_word in enumerate(self.machine_code):
            if i < len(self.memory):
                self.memory[i] = code_word.replace('_', '') # Store as raw binary string
            else:
                print(f"Warning: Machine code too large for memory. Truncated at {len(self.memory)} words.")
                break
        # print(f"Loaded to memory: {self.memory[:5]}")


    def fetch(self):
        if not (0 <= self.pc < len(self.memory)):
            print(f"PC out of bounds: {self.pc}")
            self.halted = True
            return None
        instruction_word = self.memory[self.pc]
        # print(f"Fetched PC={self.pc}: {instruction_word}")
        return instruction_word # Should be "XXXXXXXXXXXXXXXX"

    def decode_and_execute(self, instruction_word):
        """
Decodes and executes a single 16-bit instruction word (string).
This is the core of the simulator and needs to implement logic for each instruction.
        """
        if instruction_word is None or len(instruction_word) != 16:
            self.halted = True
            print(f"Invalid instruction word: {instruction_word} at PC={self.pc}")
            return

        opcode = instruction_word[-4:] # Last 4 bits are opcode in your assembler
        # print(f"  Opcode: {opcode}")
        next_pc = self.pc + 1 # Default next PC

        try:
            # R-type: rs2(4) rs1(4) rd(4) opcode(4) e.g. add, sub, and, or
            if opcode in [opcode_map['add'], opcode_map['sub'], opcode_map['and'], opcode_map['or']]:
                rd_bin = instruction_word[8:12]
                rs1_bin = instruction_word[4:8]
                rs2_bin = instruction_word[0:4]
                rd = int(rd_bin, 2)
                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                rs2_val = self.get_reg_value(int(rs2_bin, 2))

                result = 0
                if opcode == opcode_map['add']: result = rs1_val + rs2_val
                elif opcode == opcode_map['sub']: result = rs1_val - rs2_val
                elif opcode == opcode_map['and']: result = rs1_val & rs2_val
                elif opcode == opcode_map['or']:  result = rs1_val | rs2_val
                self.set_reg_value(rd, result)
                # print(f"  R-Type: op={opcode} rd={rd} rs1_val={rs1_val} rs2_val={rs2_val} -> result={result}")

            # I-type (addi, subi): imm(4) rs1(4) rd(4) opcode(4)
            elif opcode in [opcode_map['addi'], opcode_map['subi']]:
                rd_bin = instruction_word[8:12]
                rs1_bin = instruction_word[4:8]
                imm_bin_val = instruction_word[0:4]
                rd = int(rd_bin, 2)
                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                imm = self.signed_int(imm_bin_val, 4) # Convert 4-bit 2's complement to int

                result = 0
                if opcode == opcode_map['addi']: result = rs1_val + imm
                elif opcode == opcode_map['subi']: result = rs1_val - imm # Your ISA has subi
                self.set_reg_value(rd, result)
                # print(f"  I-Type (addi/subi): op={opcode} rd={rd} rs1_val={rs1_val} imm={imm} -> result={result}")


            # I-type (Load: lb, lw): imm(4) rs1(4) rd(4) opcode(4)
            elif opcode in [opcode_map['lb'], opcode_map['lw']]:
                rd_bin = instruction_word[8:12]
                rs1_bin = instruction_word[4:8] # base register
                imm_bin_val = instruction_word[0:4] # offset
                rd = int(rd_bin, 2)
                base_addr = self.get_reg_value(int(rs1_bin, 2))
                offset = self.signed_int(imm_bin_val, 4)
                mem_addr = (base_addr + offset) & 0xFFFF # Memory addresses are 16-bit

                if not (0 <= mem_addr < len(self.memory)): # Check word address for lw
                    print(f"Memory access out of bounds: addr={mem_addr} (word)")
                    self.halted = True; return

                if opcode == opcode_map['lw']:
                    # Assuming memory stores 16-bit words as binary strings "XXXXXXXXXXXXXXXX"
                    word_data_str = self.memory[mem_addr]
                    loaded_val = int(word_data_str, 2)
                    self.set_reg_value(rd, loaded_val)
                    # print(f"  LW: rd={rd} addr={mem_addr} (from base={base_addr}, off={offset}) val_str={word_data_str} -> val={loaded_val}")
                elif opcode == opcode_map['lb']:
                    # lb: load byte from memory address mem_addr, sign-extend to 16 bits
                    # Memory stores 16-bit words. We need to figure out byte addressing.
                    # Assuming word-aligned memory. If mem_addr is byte address:
                    word_addr = mem_addr // 2
                    byte_offset_in_word = mem_addr % 2 # 0 for high byte, 1 for low byte (or vice versa)

                    if not (0 <= word_addr < len(self.memory)):
                        print(f"Memory access out of bounds for LB: addr={mem_addr} (byte), word_addr={word_addr}")
                        self.halted = True; return

                    word_data_str = self.memory[word_addr] # "HHLLLLLLHHHHHHHH"
                    byte_val = 0
                    if byte_offset_in_word == 0: # Assuming high byte is at the lower address (Big Endian like)
                        # or if it's little endian and word is [Byte1 Byte0] then mem_addr points to Byte0.
                        # Your `_data_lma` format: `byte1_byte2`.
                        # If memory[idx] = "B1B1B1B1B1B1B1B1B0B0B0B0B0B0B0B0"
                        # and byte1 is at lower address:
                        byte_str = word_data_str[0:8] # Higher byte in the string
                    else: # byte_offset_in_word == 1
                        byte_str = word_data_str[8:16] # Lower byte in the string

                    loaded_byte = self.signed_int(byte_str, 8) # Sign extend from 8 to 16 bits
                    self.set_reg_value(rd, loaded_byte)
                    # print(f"  LB: rd={rd} byte_addr={mem_addr} word_addr={word_addr} byte_off={byte_offset_in_word} byte_str={byte_str} -> val={loaded_byte}")


            # S-type (Store: sb, sw): rt(4) rs1(4) imm(4) opcode(4) (Your format was rt,rs,imm,op)
            # rt is source reg (rs2 in standard), rs1 is base reg
            elif opcode in [opcode_map['sb'], opcode_map['sw']]:
                imm_bin_val = instruction_word[8:12] # Your assembler puts imm here for S-type like
                rs1_bin = instruction_word[4:8]      # Base register
                rt_bin = instruction_word[0:4]       # Source register rt (value to store)

                rt_val = self.get_reg_value(int(rt_bin, 2))
                base_addr = self.get_reg_value(int(rs1_bin, 2))
                offset = self.signed_int(imm_bin_val, 4)
                mem_addr = (base_addr + offset) & 0xFFFF

                if not (0 <= mem_addr < len(self.memory)): # Check word address for sw
                    print(f"Memory access out of bounds: addr={mem_addr} (word)")
                    self.halted = True; return

                if opcode == opcode_map['sw']:
                    # Store 16-bit word rt_val into memory[mem_addr]
                    self.memory[mem_addr] = format(rt_val & 0xFFFF, '016b')
                    # print(f"  SW: rt_val={rt_val} to addr={mem_addr} (from base={base_addr}, off={offset})")
                elif opcode == opcode_map['sb']:
                    # sb: store byte (lower 8 bits of rt_val) to memory address mem_addr
                    word_addr = mem_addr // 2
                    byte_offset_in_word = mem_addr % 2

                    if not (0 <= word_addr < len(self.memory)):
                        print(f"Memory access out of bounds for SB: addr={mem_addr} (byte), word_addr={word_addr}")
                        self.halted = True; return

                    byte_to_store_str = format(rt_val & 0xFF, '08b') # Lower 8 bits
                    current_word_str = self.memory[word_addr]
                    new_word_str = ""
                    if byte_offset_in_word == 0: # High byte
                        new_word_str = byte_to_store_str + current_word_str[8:16]
                    else: # Low byte
                        new_word_str = current_word_str[0:8] + byte_to_store_str
                    self.memory[word_addr] = new_word_str
                    # print(f"  SB: rt_val_byte={byte_to_store_str} to byte_addr={mem_addr} (word_addr={word_addr}, byte_off={byte_offset_in_word})")


            # U-type (lui): imm(8) rd(4) opcode(4)
            elif opcode == opcode_map['lui']:
                rd_bin = instruction_word[8:12]
                imm_bin_val = instruction_word[0:8] # 8-bit immediate
                rd = int(rd_bin, 2)
                imm = int(imm_bin_val, 2) # LUI imm is usually treated as unsigned upper bits
                # LUI typically does rd = imm << (some_shift_amount, e.g., 12 in RV32)
                # Your LUI seems to just load the 8-bit imm into rd, then addi handles lower bits.
                # If `li rX, 0xABCD` -> `lui rX, 0xAB` then `addi rX, rX, 0xC` then `addi rX, rX, 0xD`.
                # So, `lui rX, 0xAB` means `rX = 0xAB00` effectively, or just loads 0xAB and expects addi.
                # Based on your `li` expansion, `lui` puts `upper_8_bits` into the register,
                # which implies these are the *upper* bits of the target value.
                # So, `lui rd, val` should result in `rd = val << 8` if it's a 16-bit system.
                # Let's assume `val` is placed directly, and `addi` will shift. No, `addi` just adds.
                # So, `lui rd, imm_val` should place `imm_val << 8` into `rd`.
                # The `assemble_line` for `lui` takes `imm_val` (0-255) and formats it as `08b`.
                # The `li` pseudo-instruction: `lui rd, upper_8_bits`. This `upper_8_bits` is `(target_val >> 8) & 0xFF`.
                # So if `target_val` is `0xABCD`, `upper_8_bits` is `0xAB`.
                # `lui rd, 0xAB` should make `rd = 0xAB00`.
                self.set_reg_value(rd, imm << 8)
                # print(f"  LUI: rd={rd} imm_raw={imm} -> val={imm << 8}")

            # SB-type (beq, ble): rs2(4) rs1(4) imm(4) opcode(4)
            # Your assembler: rs2 + rs1 + imm + opcode
            elif opcode in [opcode_map['beq'], opcode_map['ble']]:
                imm_bin_val = instruction_word[8:12]
                rs1_bin = instruction_word[4:8]
                rs2_bin = instruction_word[0:4]

                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                rs2_val = self.get_reg_value(int(rs2_bin, 2))
                # Offset is PC-relative. PC is currently pointing to this branch instruction.
                # Target address = PC_current_branch_instr + (signed_offset * N)
                # In many RISC ISAs, offset is for words (multiplied by 2 or 4).
                # Your `resolve_labels` calculates offset as:
                #   `offset = target_pc_index - current_pc_index - 1`
                # This implies the offset is a direct instruction count.
                # So, `next_pc = current_pc_index + 1 + offset`.
                offset = self.signed_int(imm_bin_val, 4)

                branch_taken = False
                if opcode == opcode_map['beq']:
                    if rs1_val == rs2_val: branch_taken = True
                elif opcode == opcode_map['ble']:
                    if rs1_val <= rs2_val: branch_taken = True # rs1 <= rs2

                if branch_taken:
                    next_pc = self.pc + 1 + offset # PC is current instruction, +1 for normal flow, then add offset
                    # print(f"  BRANCH taken: op={opcode} rs1_val={rs1_val} rs2_val={rs2_val} offset={offset} -> new_pc={next_pc}")
                # else:
                # print(f"  BRANCH not taken: op={opcode} rs1_val={rs1_val} rs2_val={rs2_val} offset={offset}")


            # UJ-type (jal): imm(8) rd(4) opcode(4)
            # Your assembler: imm + rd + opcode
            elif opcode == opcode_map['jal']:
                rd_bin = instruction_word[8:12] # bits 4-7 from right
                imm_bin_val = instruction_word[0:8] # bits 8-15 from right (most significant)
                rd = int(rd_bin, 2)
                # JAL immediate is also an offset, similar to branches.
                # `offset = target_pc_index - current_pc_index - 1`
                offset = self.signed_int(imm_bin_val, 8) # 8-bit signed offset

                if rd != 0: # Save PC+1 to rd (return address)
                    self.set_reg_value(rd, (self.pc + 1) & 0xFFFF)
                next_pc = self.pc + 1 + offset
                # print(f"  JAL: rd={rd} offset={offset} -> ret_addr={(self.pc+1)&0xFFFF}, new_pc={next_pc}")


            # I-type (jalr): imm(4) rs1(4) rd(4) opcode(4)
            # Your assembler: imm + rs + rd + opcode
            elif opcode == opcode_map['jalr']:
                rd_bin = instruction_word[8:12]
                rs1_bin = instruction_word[4:8]
                imm_bin_val = instruction_word[0:4]
                rd = int(rd_bin, 2)
                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                offset = self.signed_int(imm_bin_val, 4)

                target_addr = (rs1_val + offset) & 0xFFFF
                if rd != 0:
                    self.set_reg_value(rd, (self.pc + 1) & 0xFFFF)
                next_pc = target_addr # Jumps to target_addr
                # print(f"  JALR: rd={rd} rs1_val={rs1_val} offset={offset} -> ret_addr={(self.pc+1)&0xFFFF}, new_pc={next_pc}")

            else:
                print(f"Unknown or unimplemented opcode: {opcode} for instruction {instruction_word}")
                self.halted = True
                return

            self.pc = next_pc

        except Exception as e:
            print(f"Error during execution of {instruction_word} at PC={self.pc}: {e}")
            import traceback
            traceback.print_exc()
            self.halted = True

        # Enforce r0 is always 0 after every instruction
        self.registers[register_alias['r0']] = 0


    def signed_int(self, binary_string, bits):
        """Converts a two's complement binary string to a signed integer."""
        val = int(binary_string, 2)
        if (val & (1 << (bits - 1))) != 0: # if sign bit is set
            val = val - (1 << bits)        # compute negative value
        return val

    def step(self):
        if self.halted:
            print("Cannot step, simulator halted.")
            return False

        if not (0 <= self.pc < len(self.memory) and self.memory[self.pc] != "0000000000000000"): # Halt on all zeros if desired
            # Check if it's beyond loaded machine code or explicitly halted
            num_meaningful_opcodes = 0
            for op_ in self.machine_code:
                if op_ != "0000_0000_0000_0000":
                    num_meaningful_opcodes +=1
            if self.pc >= num_meaningful_opcodes: # or self.pc >= len(self.machine_code)
                print(f"Halted: PC ({self.pc}) reached end of program or zeroed memory.")
                self.halted = True
                return False

        instruction = self.fetch()
        if instruction:
            self.decode_and_execute(instruction)
            self.print_regs() # For debugging
            return True
        else:
            self.halted = True
            print("Halted: Fetch failed or PC out of bounds.")
            return False

    def run_program(self, max_steps=1000): # Add max_steps to prevent infinite loops during dev
        print("Running program...")
        steps = 0
        while not self.halted and steps < max_steps:
            if not self.step(): # step returns False if it halts
                break
            steps += 1
        if steps >= max_steps:
            print(f"Halted: Reached max execution steps ({max_steps}).")
            self.halted = True
        self.print_regs()

    def print_regs(self):
        print("--- Registers ---")
        for i in range(0, 16, 4):
            row = []
            for j in range(4):
                reg_idx = i + j
                reg_name = reg_num_to_name.get(reg_idx, f'r{reg_idx}')
                val = self.get_reg_value(reg_idx)
                row.append(f"{reg_name:>3}: {val:<5} (0x{val:04X})")
            print(" | ".join(row))
        print(f"PC: {self.pc} (0x{self.pc:04X})")
        print("-----------------")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("16-bit ISA Simulator")
        self.simulator = Simulator16Bit()

        # Configure main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Left Pane: Code Editor and Controls
        left_pane = ttk.Frame(main_frame, padding="5")
        left_pane.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        left_pane.columnconfigure(0, weight=1)
        left_pane.rowconfigure(1, weight=1)


        # Code Input Area
        ttk.Label(left_pane, text="Assembly Code:").grid(row=0, column=0, sticky=tk.W, pady=(0,5))
        self.code_text = scrolledtext.ScrolledText(left_pane, width=60, height=20, wrap=tk.WORD, undo=True)
        self.code_text.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Control Buttons Frame
        controls_frame = ttk.Frame(left_pane)
        controls_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W + tk.E, pady=5)

        self.load_btn = ttk.Button(controls_frame, text="Load File", command=self.load_file)
        self.load_btn.pack(side=tk.LEFT, padx=2)

        self.assemble_btn = ttk.Button(controls_frame, text="Assemble", command=self.assemble_code)
        self.assemble_btn.pack(side=tk.LEFT, padx=2)

        self.step_btn = ttk.Button(controls_frame, text="Step", command=self.step_code, state=tk.DISABLED)
        self.step_btn.pack(side=tk.LEFT, padx=2)

        self.run_btn = ttk.Button(controls_frame, text="Run", command=self.run_code, state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=2)

        self.reset_btn = ttk.Button(controls_frame, text="Reset Sim", command=self.reset_simulator, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=2)

        # Status Bar (simple label for messages)
        self.status_label = ttk.Label(left_pane, text="Status: Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5,0))


        # Right Pane: Registers and Memory (later)
        right_pane = ttk.Frame(main_frame, padding="5")
        right_pane.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        right_pane.columnconfigure(0, weight=1)

        ttk.Label(right_pane, text="Registers:").grid(row=0, column=0, sticky=tk.W)
        self.reg_labels = {}
        reg_frame = ttk.Frame(right_pane)
        reg_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        for i in range(16):
            reg_name = reg_num_to_name.get(i, f'r{i}')
            ttk.Label(reg_frame, text=f"{reg_name:>3}:").grid(row=i, column=0, sticky=tk.W, padx=2)
            self.reg_labels[i] = ttk.Label(reg_frame, text="0 (0x0000)", width=15, relief=tk.GROOVE)
            self.reg_labels[i].grid(row=i, column=1, sticky=tk.W, padx=2)

        self.pc_label_title = ttk.Label(reg_frame, text="PC:")
        self.pc_label_title.grid(row=16, column=0, sticky=tk.W, padx=2, pady=(5,0))
        self.pc_label_val = ttk.Label(reg_frame, text="0 (0x0000)", width=15, relief=tk.GROOVE)
        self.pc_label_val.grid(row=16, column=1, sticky=tk.W, padx=2, pady=(5,0))

        # Memory View (placeholder)
        ttk.Label(right_pane, text="Memory View (first 16 words):").grid(row=2, column=0, sticky=tk.W, pady=(10,0))
        self.mem_labels = []
        mem_frame = ttk.Frame(right_pane)
        mem_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        for i in range(16): # Display first 16 words
            addr_label = ttk.Label(mem_frame, text=f"0x{i:03X}:")
            addr_label.grid(row=i, column=0, sticky=tk.W, padx=2)
            val_label = ttk.Label(mem_frame, text="0000_0000_0000_0000", font=("Courier", 10), relief=tk.GROOVE)
            val_label.grid(row=i, column=1, sticky=tk.W, padx=2)
            self.mem_labels.append(val_label)


        # Configure column weights for resizing
        main_frame.columnconfigure(0, weight=1) # Left pane (code)
        main_frame.columnconfigure(1, weight=0) # Right pane (registers) - fixed width for now

        self.update_ui_state() # Initial UI update

    def update_ui_state(self):
        # Update register display
        for i in range(16):
            val = self.simulator.get_reg_value(i)
            self.reg_labels[i].config(text=f"{val} (0x{val:04X})")
        # Update PC display
        pc_val = self.simulator.pc
        self.pc_label_val.config(text=f"{pc_val} (0x{pc_val:04X})")

        # Update Memory View (first 16 words)
        for i in range(min(16, len(self.simulator.memory))):
            mem_word_bin = self.simulator.memory[i] # Stored as "XXXXXXXXXXXXXXXX"
            if len(mem_word_bin) == 16:
                # Format as "XXXX_XXXX_XXXX_XXXX"
                formatted_mem_word = '_'.join([mem_word_bin[j:j+4] for j in range(0, 16, 4)])
                self.mem_labels[i].config(text=formatted_mem_word)
            else:
                self.mem_labels[i].config(text=mem_word_bin) # Should not happen if loaded correctly


        # Update button states
        if self.simulator.halted or not self.simulator.machine_code:
            self.step_btn.config(state=tk.DISABLED)
            self.run_btn.config(state=tk.DISABLED)
        else:
            self.step_btn.config(state=tk.NORMAL)
            self.run_btn.config(state=tk.NORMAL)

        if self.simulator.machine_code:
            self.reset_btn.config(state=tk.NORMAL)
        else:
            self.reset_btn.config(state=tk.DISABLED)


    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="Open Assembly File",
            filetypes=(("Assembly files", "*.asm *.s *.txt"), ("All files", "*.*"))
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.code_text.delete('1.0', tk.END)
                    self.code_text.insert('1.0', f.read())
                self.status_label.config(text=f"Loaded: {filepath}")
            except Exception as e:
                self.status_label.config(text=f"Error loading file: {e}")

    def assemble_code(self):
        self.status_label.config(text="Assembling...")
        self.root.update_idletasks() # Refresh UI to show "Assembling..."

        asm_code = self.code_text.get('1.0', tk.END)
        asm_lines = asm_code.splitlines()

        success, message = self.simulator.load_program_from_source(asm_lines)

        if success:
            self.status_label.config(text="Assembly successful. Ready to run/step.")
            self.simulator.halted = False # Ready to run
        else:
            self.status_label.config(text=f"Assembly failed: {message}")
            self.simulator.halted = True # Cannot run

        self.update_ui_state()

    def step_code(self):
        if self.simulator.step():
            self.status_label.config(text=f"Stepped. PC = {self.simulator.pc}")
        else:
            self.status_label.config(text="Simulator halted.")
        self.update_ui_state()

    def run_code(self):
        self.status_label.config(text="Running...")
        self.root.update_idletasks()
        # For a responsive GUI during run, you might need to run the simulator
        # in a separate thread or use root.after to schedule steps.
        # For now, a simple blocking run with a max_steps.
        self.simulator.run_program(max_steps=10000) # Limit steps
        self.status_label.config(text=f"Run complete. PC = {self.simulator.pc}. Halted: {self.simulator.halted}")
        self.update_ui_state()

    def reset_simulator(self):
        self.simulator.reset()
        self.status_label.config(text="Simulator reset.")
        self.update_ui_state()


if __name__ == '__main__':
    # --- Critical: Replace these placeholders with your actual assembler functions ---
    # You need to copy your `expand_pseudo_instructions`, `resolve_labels`,
    # and `assemble_line` functions from your original script into the space
    # marked "Placeholder for your existing assembler functions" above,
    # or ensure they are correctly imported if in a separate file.
    # The current placeholders are VERY basic and will not work for complex code.
    # Make sure they match the interface (arguments and return values) expected by
    # `Simulator16Bit.load_program_from_source`.
    #
    # For example, your `assemble_line` needs to correctly parse various instruction formats.
    # Your `expand_pseudo_instructions` needs to handle labels and pseudo-ops correctly.
    # Your `resolve_labels` needs to calculate offsets.
    # -------------------------------------------------------------------------------

    # Example to make the placeholder `assemble_line` slightly more functional for testing `lui` and `addi`
    # You should replace this with YOUR actual functions.
    _original_opcode_map = opcode_map.copy()
    _original_reg_alias = register_alias.copy()
    _original_reg_bin = reg_bin
    _original_imm_bin = imm_bin

    # --- Start of your actual assembler code ---
    # Copy your `opcode_map`, `register_alias` here if they are different
    # Copy your `reg_bin`, `imm_bin`, `strip_comments` here
    # Copy your `expand_pseudo_instructions`, `resolve_labels`, `assemble_line` here
    # --- Make sure they are defined globally or within the Simulator/App class if appropriate ---

    # ---- Example of where your functions would go (replace with your actual code) ----
    # opcode_map = { ... your definitions ... }
    # register_alias = { ... your definitions ... }
    # def reg_bin(reg_name): ...
    # def imm_bin(val, bits=4): ...
    # def strip_comments(line): ...
    # def expand_pseudo_instructions(lines): ...
    # def resolve_labels(expanded_lines, label_map): ...
    # def assemble_line(line): ...
    # ---- End of your actual assembler code section ----

    # Restore original placeholders if user doesn't fill them in, to avoid NameError for now
    # (This is just for the provided snippet to run without the user immediately pasting their code)
    if 'opcode_map' not in globals(): opcode_map = _original_opcode_map
    if 'register_alias' not in globals(): register_alias = _original_reg_alias
    if 'reg_bin' not in globals() or reg_bin.__doc__ is None : reg_bin = _original_reg_bin # approx check
    if 'imm_bin' not in globals() or imm_bin.__doc__ is None : imm_bin = _original_imm_bin


    root = tk.Tk()
    app = App(root)
    root.mainloop()