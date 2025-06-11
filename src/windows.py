import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import re
import time
import pseudo as pse # 导入pseudo.py

def resolve_labels(expanded_lines, label_map):
    resolved = []
    for idx, line in enumerate(expanded_lines):
        processed_line_for_tokens = line.replace(',', '').replace('(', ' ').replace(')', '')
        tokens = processed_line_for_tokens.split()

        if not tokens:
            continue
        instr = tokens[0]

        # 只关心跳转和分支指令中的标签解析
        if instr in ['ble', 'beq', 'jal']:
            if len(tokens) < 2: # 至少需要指令和1个参数
                resolved.append(line)
                continue

            last_arg = tokens[-1]

            try:
                # 如果最后一个参数已经是数字，则不是标签，直接使用
                int(last_arg, 0)
                resolved.append(line)

            except ValueError:
                # 最后一个参数不是数字，是需要解析的标签
                label_name = last_arg
                if label_name not in label_map:
                    raise KeyError(f"错误: 未定义的标签 '{label_name}' 在指令中被使用: '{line}' (在扩展后指令列表的索引 {idx})")

                # 使用标签映射中正确的PC地址，不再加1
                target_pc_index = label_map[label_name]

                current_pc_index = idx
                offset = target_pc_index - current_pc_index - 1

                temp_tokens = tokens[:-1] + [str(offset)]
                resolved.append(' '.join(temp_tokens))

        # 伪指令`la` 展开成的 `lui` 指令也需要解析标签
        elif instr == 'lui':
            if len(tokens) < 3:
                raise ValueError(f"格式错误的 LUI 指令: '{line}' at expanded index {idx}")

            immediate_or_label_arg = tokens[2]
            if immediate_or_label_arg in label_map:
                label_value = label_map[immediate_or_label_arg]
                temp_tokens = list(tokens)
                temp_tokens[2] = f'0x{label_value:X}' # 替换为十六进制地址
                resolved.append(' '.join(temp_tokens))

            else:
                resolved.append(line) # 如果不是标签，直接通过

        else:
            # 其他所有指令直接通过
            resolved.append(line)

    return resolved


class Simulator16Bit:
    def __init__(self):
        self.registers = [0] * 16  # r0 到 r15
        self.memory = ["0000_0000_0000_0000"] * 16384 # 内存大小,16384,即 0x4000
        self.pc = 0
        self.previous_pc = 0
        self.halted = False
        self.machine_code = [] # 在加载到内存之前存储汇编代码
        self.label_map = {}
        self.pc_to_source_line_map = [] # 存储PC到源码行的映射

        self.OPCODE_MAP = pse.opcode_map
        self.REGISTER_ALIAS = pse.register_alias

        # 将 r0 初始化为 0
        self.registers[register_alias['r0']] = 0

    def reset(self):
        self.registers = [0] * 16
        self.pc = 0
        self.previous_pc = 0
        self.halted = False
        # 可以从 self.machine_code 清除或重新加载 self.memory
        self.load_machine_code_to_memory() # 重新加载机器代码
        print("Simulator Reset.")
        self.print_regs()

    def get_reg_value(self, reg_idx):
        if not (0 <= reg_idx <= 15):
            raise ValueError(f"Invalid register index: {reg_idx}")

        if reg_idx == register_alias['r0']: # 确保 r0 为 0
            return 0

        return self.registers[reg_idx]

    def set_reg_value(self, reg_idx, value):
        if not (0 <= reg_idx <= 15):
            raise ValueError(f"Invalid register index: {reg_idx}")

        if reg_idx != register_alias['r0']: # r0 恒 0
            # 值为 16 位，必要时模拟溢出
            self.registers[reg_idx] = value & 0xFFFF # 确保 16 位

        else:
            self.registers[reg_idx] = 0 # r0 恒 0

    def load_program_from_source(self, expanded_instr, label_map, data_lma_values, source_lines_for_expanded):
        # 将汇编代码转换为机器码，并将其存储在内部
        self.pc_to_source_line_map = [] # 重置映射
        self.machine_code = []      # 重置机器码存储

        try:
            # 1. 解析标签 (使用 resolve_labels)
            resolved_instr_for_sim = resolve_labels(expanded_instr, label_map)

            self.pc_to_source_line_map = source_lines_for_expanded

            # 2. 组装 (使用 pseudo.py 的 assemble_line)
            raw_machine_code_for_sim = []

            for line_content in resolved_instr_for_sim:

                if line_content.strip():
                    bin_code = pse.assemble_line(line_content.strip())
                    raw_machine_code_for_sim.append(bin_code)

            # 3. 准备并加载到模拟器内存
            rom_output_lines = []
            for i, code in enumerate(raw_machine_code_for_sim):

                if i < 128: # 假设ROM大小为256
                    rom_output_lines.append('_'.join([code[j:j+4] for j in range(0, 16, 4)]))

            while len(rom_output_lines) < 128:
                rom_output_lines.append("0000_0000_0000_0000")

            if len(raw_machine_code_for_sim) > 128:
                print(f"警告: ... ROM区限制为128行...")

            data_output_lines = []
            k = 0
            while k < len(data_lma_values):
                byte1_val = data_lma_values[k]; byte1_bin = format(byte1_val, '08b')
                byte1_formatted = f"{byte1_bin[0:4]}_{byte1_bin[4:8]}"

                if k + 1 < len(data_lma_values):
                    byte2_val = data_lma_values[k+1]; byte2_bin = format(byte2_val, '08b')
                    byte2_formatted = f"{byte2_bin[0:4]}_{byte2_bin[4:8]}"

                else:
                    byte2_formatted = "0000_0000"
                data_output_lines.append(f"{byte1_formatted}_{byte2_formatted}")
                k += 2

            # self.machine_code 存储的是模拟器将要使用的、格式化后的机器码
            self.machine_code = rom_output_lines + data_output_lines
            self.load_machine_code_to_memory()

            self.pc = 0
            self.halted = False
            return True, "汇编成功 (模拟器已加载代码)."

        except Exception as e:
            self.machine_code = []
            self.pc_to_source_line_map = []
            import traceback; traceback.print_exc()
            return False, f"加载到模拟器时出错: {e}"

    def load_machine_code_to_memory(self):
        self.memory = ["0000_0000_0000_0000"] * len(self.memory) # 先清除内存
        # 将汇编程序加载到内存中
        for i, formatted_code_word in enumerate(self.machine_code):
            if i < len(self.memory): # 防止超出预设的 self.memory 大小
                # 移除下划线，得到纯二进制字符串
                raw_binary_word = formatted_code_word.replace('_', '')

                if len(raw_binary_word) == 16 and all(c in '01' for c in raw_binary_word):
                    self.memory[i] = raw_binary_word

                else:
                    print(f"警告: 机器码 \"{formatted_code_word}\" 格式不正确，跳过加载到内存地址 {i}")
                    self.memory[i] = "0000000000000000" # 或者其他错误标记

            else:
                print(f"警告: 机器码数量 ({len(self.machine_code)}) 超出内存容量 ({len(self.memory)})。部分代码未加载。")
                break
        # print(f"Loaded to memory: {self.memory[:5]}")

        # 如果 self.machine_code 比 self.memory 短，内存中剩余部分将保持其旧值或初始值
        # 如果需要用0填充剩余内存
        for i in range(len(self.machine_code), len(self.memory)):
            self.memory[i] = "0000000000000000"


    def fetch(self):
        if not (0 <= self.pc < len(self.memory)):
            print(f"PC out of bounds: {self.pc}")
            self.halted = True
            return None
        instruction_word = self.memory[self.pc]

        # print(f"Fetched PC={self.pc}: {instruction_word}")
        return instruction_word # 形式:"XXXXXXXXXXXXXXXX"

    def decode_and_execute(self, instruction_word):
    # 解码并执行单条16位指令字 (字符串格式 "XXXXXXXXXXXXXXXX")。

        if instruction_word is None or len(instruction_word) != 16 or \
        not all(c in '01' for c in instruction_word):
            self.halted = True
            print(f"错误: 无效的指令字 '{instruction_word}' 在 PC={self.pc}")
            return

        # 默认情况下，PC指向下一条指令
        next_pc = self.pc + 1

        try:
            # 字段解析顺序与 assemble_line 的拼接顺序相反
            # instr[0:...] 是高位, instr[...:16] 是低位
            # Opcode 总是最后4位 (bits 3-0)
            opcode = instruction_word[12:16]

            #  R-type: add, sub, and, or
            # 格式: rs2(4) + rs1(4) + rd(4) + opcode(4)
            if opcode in [self.OPCODE_MAP['add'], self.OPCODE_MAP['sub'], self.OPCODE_MAP['and'], self.OPCODE_MAP['or']]:
                rs2_bin = instruction_word[0:4]
                rs1_bin = instruction_word[4:8]
                rd_bin  = instruction_word[8:12]
                rd = int(rd_bin, 2)
                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                rs2_val = self.get_reg_value(int(rs2_bin, 2))

                result = 0
                if opcode == self.OPCODE_MAP['add']: result = rs1_val + rs2_val
                elif opcode == self.OPCODE_MAP['sub']: result = rs1_val - rs2_val
                elif opcode == self.OPCODE_MAP['and']: result = rs1_val & rs2_val
                elif opcode == self.OPCODE_MAP['or']:  result = rs1_val | rs2_val
                self.set_reg_value(rd, result)

            #  I-type (算术): addi, subi
            # 格式: imm(4) + rs1(4) + rd(4) + opcode(4)
            elif opcode in [self.OPCODE_MAP['addi'], self.OPCODE_MAP['subi']]:
                imm_bin = instruction_word[0:4]
                rs1_bin = instruction_word[4:8]
                rd_bin  = instruction_word[8:12]
                rd = int(rd_bin, 2)
                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                imm_val = self.signed_int(imm_bin, 4) # 4位有符号立即数

                result = 0
                if opcode == self.OPCODE_MAP['addi']: result = rs1_val + imm_val
                elif opcode == self.OPCODE_MAP['subi']: result = rs1_val - imm_val
                self.set_reg_value(rd, result)

            #  I-type (加载): lw, lb
            # 格式: imm(4) + rs1(4) + rd(4) + opcode(4)
            elif opcode in [self.OPCODE_MAP['lb'], self.OPCODE_MAP['lw']]:
                imm_bin = instruction_word[0:4]
                rs1_bin = instruction_word[4:8]
                rd_bin  = instruction_word[8:12]
                rd = int(rd_bin, 2)
                base_addr = self.get_reg_value(int(rs1_bin, 2))
                offset = self.signed_int(imm_bin, 4)
                mem_addr = (base_addr + offset) & 0xFFFF

                # # 调试
                # print("\n--- DEBUG: 执行加载指令 ---")
                # print(f"  指令类型: {'LB' if opcode == self.OPCODE_MAP['lb'] else 'LW'}")
                # print(f"  目标寄存器(rd): r{rd}")
                # print(f"  基址寄存器(rs1)值: {base_addr} (0x{base_addr:04X})")
                # print(f"  偏移量(imm): {offset}")
                # print(f"  计算出的源内存地址: 0x{mem_addr:04X}")

                word_addr = mem_addr // 2

                if not (0 <= word_addr < len(self.memory)):
                    print(f"  错误: 源地址 0x{word_addr:04X} 超出内存范围！")
                    self.halted = True; return

                word_data_str = self.memory[word_addr]
                # print(f"  从内存字地址 0x{word_addr:04X} 读取到内容: '{word_data_str}'")

                if opcode == self.OPCODE_MAP['lw']:
                    loaded_val = int(word_data_str, 2)
                    print(f"  LW: 准备将值 {loaded_val} (0x{loaded_val:04X}) 存入 r{rd}")
                    self.set_reg_value(rd, loaded_val)

                elif opcode == self.OPCODE_MAP['lb']:
                    byte_offset_in_word = mem_addr % 2
                    byte_str = word_data_str[0:8] if byte_offset_in_word == 0 else word_data_str[8:16]
                    loaded_byte_signed = self.signed_int(byte_str, 8)
                    # print(f"  LB: 从字中提取的字节为 '{byte_str}', 符号扩展后值为 {loaded_byte_signed}")
                    # print(f"  LB: 准备将值 {loaded_byte_signed} (0x{loaded_byte_signed & 0xFFFF:04X}) 存入 r{rd}")
                    self.set_reg_value(rd, loaded_byte_signed)

                # print(f"  加载后, r{rd} 的值是: {self.get_reg_value(rd)}")
                # print("--- DEBUG: 加载指令执行完毕 ---\n")

            # S-type 指令 (存储): sb, sw
            elif opcode in [self.OPCODE_MAP['sb'], self.OPCODE_MAP['sw']]:
                rt_bin  = instruction_word[0:4] # 源寄存器 (rs2)
                rs1_bin = instruction_word[4:8] # 基址寄存器
                imm_bin = instruction_word[8:12] # 偏移量

                rt_val = self.get_reg_value(int(rt_bin, 2))
                base_addr = self.get_reg_value(int(rs1_bin, 2))
                offset = self.signed_int(imm_bin, 4)
                mem_addr = (base_addr + offset) & 0xFFFF

                # # 调试
                # print("\n--- DEBUG: 执行存储指令 ---")
                # print(f"  指令类型: {'SB' if opcode == self.OPCODE_MAP['sb'] else 'SW'}")
                # print(f"  源寄存器(rt) r{int(rt_bin,2)} 的值: {rt_val} (0x{rt_val:04X})")
                # print(f"  基址寄存器(rs1) r{int(rs1_bin,2)} 的值: {base_addr} (0x{base_addr:04X})")
                # print(f"  偏移量(imm): {offset}")
                # print(f"  计算出的目标内存地址: 0x{mem_addr:04X}")

                word_addr = mem_addr // 2

                if not (0 <= word_addr < len(self.memory)):
                    print(f"  错误: 目标地址 0x{word_addr:04X} 超出内存范围！")
                    self.halted = True; return

                current_word_str = self.memory[word_addr]
                # print(f"  写入前，内存字地址 0x{word_addr:04X} 的内容: '{current_word_str}'")

                if opcode == self.OPCODE_MAP['sw']:
                    word_to_store_str = format(rt_val & 0xFFFF, '016b')
                    self.memory[word_addr] = word_to_store_str

                elif opcode == self.OPCODE_MAP['sb']:
                    byte_offset_in_word = mem_addr % 2
                    byte_to_store_str = format(rt_val & 0xFF, '08b')
                    new_word_str = byte_to_store_str + current_word_str[8:16] if byte_offset_in_word == 0 else current_word_str[0:8] + byte_to_store_str
                    self.memory[word_addr] = new_word_str

                # print(f"  写入后，内存字地址 0x{word_addr:04X} 的内容: '{self.memory[word_addr]}'")
                # print("--- DEBUG: 存储指令执行完毕 ---\n")

            #  SB-type (分支): beq, ble
            # 格式: rs2(4) + rs1(4) + imm(4) + opcode(4)
            elif opcode in [self.OPCODE_MAP['beq'], self.OPCODE_MAP['ble']]:
                rs2_bin = instruction_word[0:4]
                rs1_bin = instruction_word[4:8]
                imm_bin = instruction_word[8:12]
                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                rs2_val = self.get_reg_value(int(rs2_bin, 2))
                offset = self.signed_int(imm_bin, 4) # 4位有符号指令偏移

                branch_taken = False

                if opcode == self.OPCODE_MAP['beq'] and rs1_val == rs2_val: branch_taken = True
                elif opcode == self.OPCODE_MAP['ble'] and rs1_val <= rs2_val: branch_taken = True

                if branch_taken:
                    next_pc = (self.pc + 1 + offset) & 0xFFFF

            #  U-type: lui
            # 格式: imm(8) + rd(4) + opcode(4)
            elif opcode == self.OPCODE_MAP['lui']:
                imm_bin = instruction_word[0:8]
                rd_bin  = instruction_word[8:12]
                rd = int(rd_bin, 2)
                imm_val = int(imm_bin, 2) # 无符号立即数
                self.set_reg_value(rd, imm_val << 8)

            #  UJ-type: jal
            # 格式: imm(8) + rd(4) + opcode(4)
            elif opcode == self.OPCODE_MAP['jal']:
                imm_bin = instruction_word[0:8]
                rd_bin  = instruction_word[8:12]
                rd = int(rd_bin, 2)
                offset = self.signed_int(imm_bin, 8)

                if rd != 0:
                    self.set_reg_value(rd, (self.pc + 1) & 0xFFFF)

                # `resolve_labels` 中计算偏移的逻辑是 offset = target_pc - current_pc - 1
                # （其中 target_pc 被特殊处理为 label_map[label_name] + 1）
                # 模拟器中执行时，只需应用该偏移： next_pc = current_pc + 1 + offset
                next_pc = (self.pc + 1 + offset) & 0xFFFF

            #  I-type: jalr
            # 格式: imm(4) + rs1(4) + rd(4) + opcode(4)
            elif opcode == self.OPCODE_MAP['jalr']:
                imm_bin = instruction_word[0:4]
                rs1_bin = instruction_word[4:8]
                rd_bin  = instruction_word[8:12]
                rd = int(rd_bin, 2)
                rs1_val = self.get_reg_value(int(rs1_bin, 2))
                offset = self.signed_int(imm_bin, 4)

                if rd != 0:
                    self.set_reg_value(rd, (self.pc + 1) & 0xFFFF)

                next_pc = (rs1_val + offset) & 0xFFFF

            else:
                print(f"错误: 未知或未实现的操作码 '{opcode}' 在 PC={self.pc:04X}, 指令={instruction_word}")
                self.halted = True
                return

            self.pc = next_pc # 更新PC

        except Exception as e:
            print(f"执行错误: PC={self.pc:04X}, 指令={instruction_word}, 错误={e}")
            import traceback
            traceback.print_exc()
            self.halted = True

        # 确保r0始终为0
        self.set_reg_value(0, 0) # 调用set_reg_value，它内部有对r0的保护逻辑


    def signed_int(self, binary_string, bits):
        # 二进制补码转换为有符号整数
        val = int(binary_string, 2)

        if (val & (1 << (bits - 1))) != 0: # 若设置了符号位
            val = val - (1 << bits)        # 计算负值
        return val

    def step(self):
        # 执行单步操作
        # 如果成功执行一条指令，则返回 True;如果模拟器已停止或无法执行，则返回 False

        # 1. 执行前检查状态
        if self.halted:
            print("模拟器已停止，无法单步执行。")
            return False

        # 检查PC是否越界或指向了全0的无效指令区域
        # (假设程序结束或无效区域用全0指令表示)
        if not (0 <= self.pc < len(self.memory) and self.memory[self.pc] != "0000000000000000"):
            self.halted = True
            print(f"模拟器在 PC={self.pc} 处停止 (PC越界或遇到无效指令).")
            return False
        self.previous_pc = self.pc
        # 2. 获取并执行指令
        instruction = self.fetch()

        if instruction:
            # decode_and_execute 会在内部处理执行，并可能在出错时设置 self.halted = True
            self.decode_and_execute(instruction)

            # 3. 返回正确的状态
            # 只要 fetch 成功，就认为这一步是“尝试过”的
            # simulator 是否继续，取决于执行后 self.halted 的状态
            # step() 的返回值表明“本次step是否成功启动”
            # decode_and_execute 出错会设置 halted，但本次 step 本身是成功发起的
            # 为了让主循环的逻辑更清晰，这里直接检查 halted 状态
            if self.halted:
                return False # 如果 decode_and_execute 内部导致了停止，则返回 False

            else:
                return True # 否则，成功执行一步，返回 True
        else:
            # Fetch 失败说明着PC有问题
            self.halted = True
            return False

    def run_program(self, max_steps=1000): # max_steps 防无限循环
        print("Running program...")

        time.sleep(0.3) # 延迟0.3s

        steps = 0
        while not self.halted and steps < max_steps:
            if not self.step(): # 返回 False，如果步骤停止
                break
            steps += 1

        if steps >= max_steps:
            print(f"Halted: Reached max execution steps ({max_steps}).")
            self.halted = True
        self.print_regs()

    def print_regs(self):
        print("--- Registers ---")

        time.sleep(0.3)  # 延迟0.3s

        for i in range(0, 16, 4):
            row = []
            for j in range(4):
                reg_idx = i + j
                reg_name = pse.reg_num_to_name.get(reg_idx, f'r{reg_idx}')
                val = self.get_reg_value(reg_idx)
                row.append(f"{reg_name:>3}: {val:<5} (0x{val:04X})")
            print(" | ".join(row))
        print(f"PC: {self.pc} (0x{self.pc:04X})")
        print("-----------------")


class App:
    def __init__(self, root):

        # #测试
        # print("从 pesudo 加载的 Opcode Map:", pse.opcode_map)
        # print("从 pseudo 加载的 Register Alias:", pse.register_alias)

        self.root = root
        self.root.title("自定义ISA的16位RISC单周期CPU")

        import tkinter.font as tkFont

        # 定义字体
        self.base_font_family = "Courier New"
        self.base_font_size = 12
        # self.code_font 用于 tk.Text 组件本身的基础字体
        self.actual_code_font = tkFont.Font(family=self.base_font_family,size=self.base_font_size)

        # UI 元素 (标签、按钮等) 使用的字体
        self.ui_font_family = "Arial"
        self.ui_font_size = 12
        self.ui_font = (self.ui_font_family, self.ui_font_size)

        self.simulator = Simulator16Bit()

        if hasattr(pse, 'reg_num_to_name'):
            self.reg_num_to_name = pse.reg_num_to_name
        else:
            self.reg_num_to_name = {i: f'r{i}' for i in range(16)}

        self.is_running_continuously = False # 追踪是否处于连续执行状态
        self._continuous_run_job = None      # 用于 after 方法的ID
        self.run_step_counter = 0

        #  语法高亮：定义标签名称列表
        self.highlight_tags = [
            'comment_tag',
            'instruction_tag',
            'pseudo_instruction_tag',
            'register_tag'
        ]

        # 断点初始化
        self.breakpoints = set() # 存储设置了断点的源文件行号 (1-based)

        main_frame = ttk.Frame(root, padding=(5, 2, 5, 5))
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # 追踪内存视图起始地址的属性
        self.memory_view_start_addr = 0

        #    代码编辑区和行号区
        # 创建一个框架来容纳行号和代码文本区
        code_area_frame = ttk.Frame(main_frame)
        code_area_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=(0, 5))
        main_frame.columnconfigure(0, weight=3)
        main_frame.rowconfigure(0, weight=1)    # 让代码区可以垂直伸展

        code_area_frame.rowconfigure(1, weight=1) # 让包含行号和文本框的行可以伸展
        code_area_frame.columnconfigure(1, weight=1) # 让代码文本框可以水平伸展

        ttk.Label(code_area_frame, text="汇编代码:").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,5))

        # 行号区 (tk.Text)
        self.line_numbers_text = tk.Text(code_area_frame, width=4, padx=1, takefocus=0, borderwidth=0,background='lightgrey', state='disabled', wrap='none',font=self.actual_code_font,spacing1=0, spacing2=0, spacing3=0)
        self.line_numbers_text.grid(row=1, column=0, sticky='ns')

        # 行号区绑定点击事件
        self.line_numbers_text.bind("<Button-1>", self.on_line_number_click)
        # 行号区的断点标记配置一个tag
        self.line_numbers_text.tag_configure("breakpoint_set_marker", foreground="red", font=self.actual_code_font)

        # 代码编辑区 (tk.Text)
        self.code_text = tk.Text(code_area_frame, width=60, height=25, borderwidth=0, wrap='none', undo=True,font=self.actual_code_font,spacing1=0, spacing2=0, spacing3=0)
        self.code_text.grid(row=1, column=1, sticky='nsew')

        # 垂直滚动条 (tk.Scrollbar)
        self.v_scrollbar = ttk.Scrollbar(code_area_frame, orient="vertical", command=self._on_scrollbar_yview)
        self.v_scrollbar.grid(row=1, column=2, sticky='ns')

        # 关联滚动条和文本区
        self.code_text.config(yscrollcommand=self._on_text_scroll)

        # 水平滚动条
        self.h_scrollbar = ttk.Scrollbar(code_area_frame, orient="horizontal", command=self.code_text.xview)
        self.h_scrollbar.grid(row=2, column=1, sticky='ew') # 放置在代码编辑区下方，只作用于代码区

        self.code_text.config(xscrollcommand=self.h_scrollbar.set)

        # 语法高亮：配置标签颜色和字体
        # 注释：绿色  指令：蓝色加粗  寄存器：红色
        self.code_text.tag_configure('comment_tag', foreground='green', font=self.actual_code_font)
        self.code_text.tag_configure('instruction_tag', foreground='blue', font=self.actual_code_font)
        self.code_text.tag_configure('pseudo_instruction_tag', foreground='blue',font=self.actual_code_font)
        self.code_text.tag_configure('register_tag', foreground='red', font=self.actual_code_font)

        # 语法高亮：绑定事件
        # on_text_change 会调用 _schedule_highlighting
        self.code_text.bind('<KeyRelease>', self.on_text_change)
        self.code_text.bind("<<Modified>>", self.on_text_modified)
        self.code_text.bind('<MouseWheel>', self._on_unified_mousewheel_scroll)
        self.code_text.bind('<Button-4>', self._on_unified_mousewheel_scroll)
        self.code_text.bind('<Button-5>', self._on_unified_mousewheel_scroll)

        # 为行号区绑定鼠标滚轮事件到同一个统一处理方法
        self.line_numbers_text.bind('<MouseWheel>', self._on_unified_mousewheel_scroll)
        self.line_numbers_text.bind('<Button-4>', self._on_unified_mousewheel_scroll)
        self.line_numbers_text.bind('<Button-5>', self._on_unified_mousewheel_scroll)

        # 控制按钮和状态栏
        # 按钮放在 code_area_frame 下方

        controls_frame = ttk.Frame(code_area_frame) # 将按钮放在代码区下方
        controls_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W + tk.E, pady=5)

        self.load_btn = ttk.Button(controls_frame, text="导入文件", command=self.load_file)
        self.load_btn.pack(side=tk.LEFT, padx=2)

        self.assemble_btn = ttk.Button(controls_frame, text="汇编", command=self.assemble_code)
        self.assemble_btn.pack(side=tk.LEFT, padx=2)

        self.step_btn = ttk.Button(controls_frame, text="单步", command=self.step_code, state=tk.DISABLED)
        self.step_btn.pack(side=tk.LEFT, padx=2)

        self.run_btn = ttk.Button(controls_frame, text="执行", command=self.run_code, state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=2)

        self.stop_btn = ttk.Button(controls_frame, text="停止", command=self.stop_continuous_run, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=2)

        self.reset_btn = ttk.Button(controls_frame, text="重置", command=self.reset_simulator, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=2)

        # self.debug_btn = ttk.Button(controls_frame, text="内存调试", command=self.debug_print_memory)
        # self.debug_btn.pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(code_area_frame, text="已就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5,0))

        #  当前执行行高亮：定义标签
        if hasattr(self, 'code_text'): # 良好的健壮性检查
            self.code_text.tag_configure('current_execution_line_tag', background='yellow')

        # 在 update_ui_state() 调用之前
        self.current_highlighted_tk_line = None # 存储当前高亮的Tkinter行号 (1-based)

        self._line_number_update_job = None
        self._highlight_job = None

        # 右侧面板：寄存器和内存视图
        right_pane = ttk.Frame(main_frame, padding=(5, 0, 5, 5))
        right_pane.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=(0, 5))
        main_frame.columnconfigure(1, weight=1) # 给 right_pane 在 main_frame 中的列分配权重

        # 配置 right_pane 使其内部可以有两列平均分配空间 (或者按需调整权重)
        right_pane.columnconfigure(0, weight=1) # 第0列用于寄存器
        right_pane.columnconfigure(1, weight=1) # 第1列用于内存
        # right_pane 的行配置，第0行放标题，第1行放具体内容并允许扩展
        right_pane.rowconfigure(0, weight=0)
        right_pane.rowconfigure(1, weight=1) # 让包含 reg_frame 和 mem_frame 的行可以垂直伸展

        ttk.Label(right_pane, text="寄存器:").grid(row=0, column=0,sticky=tk.NW, padx=(0,5), pady=(0,2))
        self.reg_frame = ttk.Frame(right_pane) # 父组件是 right_pane
        self.reg_frame.grid(row=1, column=0, sticky='nsew', padx=(0,5)) # 占据第1行，第0列

        # padx=(0,5) 在右边留一点间距
        self.reg_labels = {}

        for i in range(16):
            # 1. 从映射字典获取寄存器的主要别名 (例如 'ra', 'sp', 'a0' 等)
            primary_alias = self.reg_num_to_name.get(i, f'r{i}')

            display_text = ""
            # 2. 判断这个别名是否以 'a' 开头
            if primary_alias.startswith('a'):
                # 如果是 'a' 系列寄存器，则构建 "aX (rY):" 格式的字符串
                display_text = f"{primary_alias} (r{i}):"

            else:
                # 否则 (如 r0, ra, sp)，只显示r
                display_text = f"r{i}:"

            # 4. 创建标签，并使用 f-string 的左对齐格式化，确保所有冒号都能对齐
            #    最长的字符串可能是 "a12 (r15):"，我们需要为它留足空间
            ttk.Label(self.reg_frame, text=f"{display_text:<12}").grid(row=i, column=0, sticky=tk.W, padx=2, pady=1)

            # 创建值标签的代码保持不变
            self.reg_labels[i] = ttk.Label(self.reg_frame, text="0 (0x0000)", width=18, relief=tk.GROOVE, anchor=tk.W)
            self.reg_labels[i].grid(row=i, column=1, sticky=tk.W, padx=2, pady=1)

        # # pc计数器
        # self.pc_label_title = ttk.Label(self.reg_frame, text="PC:")
        # self.pc_label_title.grid(row=16, column=0, sticky=tk.W, padx=2, pady=(5,1))
        # self.pc_label_val = ttk.Label(self.reg_frame, text="0 (0x0000)", width=18, relief=tk.GROOVE, anchor=tk.W)
        # self.pc_label_val.grid(row=16, column=1, sticky=tk.W, padx=2, pady=(5,1))

        ttk.Label(right_pane, text="内存视图:").grid(row=0, column=1, sticky=tk.NW, padx=(5,0), pady=(0,2))

        self.mem_frame = ttk.Frame(right_pane) # 父组件:right_pane
        self.mem_frame.grid(row=1, column=1, sticky='nsew', padx=(5,0)) # 占据第1行，第1列

        # 让 mem_frame 内部的文本区可以扩展
        self.mem_frame.rowconfigure(2, weight=1)
        self.mem_frame.columnconfigure(0, weight=1)

        # 地址跳转的UI组件
        mem_nav_frame = ttk.Frame(self.mem_frame)
        mem_nav_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0,5))

        ttk.Label(mem_nav_frame, text="地址(Hex):").pack(side=tk.LEFT, padx=(0,2))
        self.mem_addr_entry = ttk.Entry(mem_nav_frame, width=10)
        self.mem_addr_entry.pack(side=tk.LEFT, padx=2)
        self.mem_addr_entry.insert(0, "1000") # 默认显示地址 0x1000
        ttk.Button(mem_nav_frame, text="跳转", command=self.go_to_memory_address).pack(side=tk.LEFT, padx=2)

        # 内存显示文本区 (tk.Text)
        self.memory_display_text = tk.Text(self.mem_frame, wrap='none', undo=False, # undo通常对显示区不需要
                                           font=self.actual_code_font, # 使用之前定义的字体
                                           width=27) # 宽度
        self.memory_display_text.grid(row=1, column=0, sticky='nsew')

        # 内存显示区的垂直滚动条
        mem_v_scrollbar = ttk.Scrollbar(self.mem_frame, orient="vertical", command=self.memory_display_text.yview)
        mem_v_scrollbar.grid(row=1, column=1, sticky='ns')
        self.memory_display_text.config(yscrollcommand=mem_v_scrollbar.set)

        # self.mem_labels = []
        # mem_frame = ttk.Frame(right_pane)
        # mem_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        # for i in range(16):
        #     addr_label = ttk.Label(self.mem_frame, text=f"0x{i:03X}:", style='Addr.TLabel')
        #     addr_label.grid(row=i, column=0, sticky=tk.W, padx=2, pady=1)
        #     val_label = ttk.Label(self.mem_frame, text="0000_0000_0000_0000", style='Memory.TLabel', relief=tk.GROOVE, anchor=tk.W)
        #     val_label.grid(row=i, column=1, sticky=tk.W, padx=2, pady=1)
        #     self.mem_labels.append(val_label)


        self._line_number_update_job = None # 用于延迟更新行号
        self._highlight_job = None
        self.is_running_continuously = False # 连续运行
        self._continuous_run_job = None


        self._highlight_job = None # 延迟高亮

        if hasattr(self, 'code_text'):
            self.code_text.tag_configure('current_execution_line_tag', background='yellow')
        self.current_highlighted_tk_line = None

        # 确保语法高亮模式定义
        if hasattr(pse, 'opcode_map') and hasattr(pse, 'register_alias'):
            self.opcodes = list(pse.opcode_map.keys())
            self.pseudo_opcodes = ['li', 'la', 'j', 'bge']
            instructions_pattern = r"\b(" + "|".join(self.opcodes) + r")\b"
            pseudo_instructions_pattern = r"\b(" + "|".join(self.pseudo_opcodes) + r")\b"
            register_names = list(pse.register_alias.keys())
            _generic_regs_pattern_str = r"\b(r(?:[0-9]|1[0-5]))\b"
            core_generic_part = _generic_regs_pattern_str[2:-2]
            sorted_reg_names = sorted(register_names, key=len, reverse=True)
            all_registers_pattern = r"\b(" + "|".join(sorted_reg_names) + r"|" + core_generic_part + r")\b"
            self.highlight_patterns = {
                'comment_tag': r"(#|//|///)[^\n]*",
                'instruction_tag': instructions_pattern,
                'pseudo_instruction_tag': pseudo_instructions_pattern,
                'register_tag': all_registers_pattern,
            }
            self.highlight_order = [
                'comment_tag', 'instruction_tag', 'pseudo_instruction_tag', 'register_tag'
            ]

        else:
            self.highlight_patterns = {}; self.highlight_order = []


        self._redraw_line_numbers()
        if hasattr(self, 'apply_syntax_highlighting'):
            self.apply_syntax_highlighting()

        # 初始化UI状态和首次加载
        self.update_ui_state()
        self.update_line_numbers()
        self.go_to_memory_address()

        hardcoded_filepath = "D:/UESTC/2.2/ZhongShe/assembler_py/src/program.txt"

        if hardcoded_filepath: # 确保路径不是空字符串
            print(f"尝试从预设路径加载文件: {hardcoded_filepath}")
            self.load_file(filepath=hardcoded_filepath)

    def on_line_number_click(self, event):
        # 处理行号区域的点击事件，用于切换断点
        try:
            # 获取点击位置对应的行号 (1-based)
            # index = self.line_numbers_text.index(f"@{event.x},{event.y}")
            # clicked_line_num_str = index.split('.')[0]
            # clicked_line_num = int(clicked_line_num_str)

            # 更可靠的方式是基于 y 计算，因为行号区宽度固定，x 可能不准
            # 或者，如果行号是简单地每行一个数字，可以用 dlineinfo
            # 假设行号区每行就是一个数字加换行
            # index = self.line_numbers_text.index(f"@0,{event.y}") # 用x=0确保在行首

            # 或者获取当前鼠标y坐标下的行开始
            # self.line_numbers_text.mark_set("click_pos", f"@{event.x},{event.y}")
            # line_start_index = self.line_numbers_text.index("click_pos linestart")

            line_start_index = self.line_numbers_text.index(f"@{event.x},{event.y} linestart")
            clicked_line_num = int(line_start_index.split('.')[0])

            # 检查点击的行号是否在有效代码行范围内
            code_lines = int(self.code_text.index('end-1c').split('.')[0]) if self.code_text.get("1.0", "end-1c").strip() else 0

            if 1 <= clicked_line_num <= code_lines: # 确保行号有效
                if clicked_line_num in self.breakpoints:
                    self.breakpoints.remove(clicked_line_num)
                    print(f"断点已移除: 第 {clicked_line_num} 行")

                else:
                    self.breakpoints.add(clicked_line_num)
                    print(f"断点已设置: 第 {clicked_line_num} 行")
                self._redraw_line_numbers() # 更新行号区的显示以反映断点变化

            else:
                print(f"无效的断点行: {clicked_line_num} (总代码行数: {code_lines})")

            # # 调试
            # print(f"--- DEBUG: 断点切换后, self.breakpoints = {self.breakpoints} ---")
            self._redraw_line_numbers()

        except ValueError: # 如果点击处无法解析为行号
            pass
        except tk.TclError: # 如果 index 无效
            pass
        return "break" # 阻止 Text 组件的默认点击行为（例如移动光标）

    def _redraw_line_numbers(self, event=None):
        # 更新行号区域的显示，并标记断点

        # # 调试
        # print(f"--- DEBUG: _redraw_line_numbers 被调用. 当前断点: {self.breakpoints} ---")

        self.line_numbers_text.config(state='normal')
        self.line_numbers_text.delete('1.0', 'end')

        lines_str = self.code_text.index('end-1c').split('.')[0]
        lines = int(lines_str) if lines_str else 1
        first_char_of_last_line = self.code_text.get(f"{lines}.0") if lines > 0 else ""
        if not self.code_text.get("1.0", "end-1c").strip() and lines == 1 and not first_char_of_last_line:
            lines = 0

        max_digits = len(str(lines)) if lines > 0 else 1

        # 宽度至少能容纳 max_digits 个字符，或者一个 "●" 加上可能的对齐空格
        # 以 max_digits 为基准宽度，让 "●" 也尽量对齐
        display_width = max_digits
        self.line_numbers_text.config(width=display_width + 1) # 加1,为了美感

        if lines > 0:
            for i in range(1, lines + 1):
                line_display_content = ""
                apply_breakpoint_tag = False

                if i in self.breakpoints:
                    # 用 "●" 代替数字，并用空格使其右对齐，占据 max_digits 宽度
                    line_display_content = "●".rjust(max_digits)
                    apply_breakpoint_tag = True

                else:
                    line_display_content = str(i).rjust(max_digits) # 数字右对齐

                full_line_in_gutter = f"{line_display_content}\n"

                # 获取插入此行前的 Tkinter 文本索引，用于精确打标签
                current_line_tk_index_str = f"{i}.0" # 行号区的第i行

                self.line_numbers_text.insert('end', full_line_in_gutter)

                if apply_breakpoint_tag:
                    # 为刚刚插入的 "●" (或整个填充后的字符串) 应用标签
                    # 注意：这里的索引是相对于 line_numbers_text 内部的
                    tag_start = current_line_tk_index_str
                    # tag_end 计算需要精确到 line_display_content 的末尾
                    tag_end = f"{current_line_tk_index_str} + {len(line_display_content)} chars"
                    self.line_numbers_text.tag_add("breakpoint_set_marker", tag_start, tag_end)

        self.line_numbers_text.config(state='disabled')
        self.line_numbers_text.update_idletasks()
        self._scroll_sync_y()

    def _schedule_highlighting(self):
        # 安排语法高亮任务，带延迟
        if self._highlight_job:
            self.root.after_cancel(self._highlight_job)
        self._highlight_job = self.root.after(200, self.apply_syntax_highlighting) # 200ms 延迟

    def apply_syntax_highlighting(self):
        # 应用语法高亮到代码编辑区
        if not hasattr(self, 'code_text') or not self.code_text.winfo_exists():
            return # 如果组件还不存在或已销毁，则不执行

        # 1. 清除旧的自定义高亮标签
        for tag in self.highlight_tags:
            self.code_text.tag_remove(tag, "1.0", "end")

        content = self.code_text.get("1.0", "end-1c") # 获取所有文本内容

        # 2. 应用新的高亮
        for tag_name in self.highlight_order:
            pattern = self.highlight_patterns.get(tag_name)
            if not pattern: continue

            flags = re.IGNORECASE

            for match in re.finditer(pattern, content, flags):
                start_index = f"1.0 + {match.start()} chars"
                end_index = f"1.0 + {match.end()} chars"
                self.code_text.tag_add(tag_name, start_index, end_index)

    def on_text_modified(self, event=None):
        # 当文本框内容被修改时（例如，undo/redo/paste），安排行号和高亮更新
        if self.code_text.edit_modified():
            # 更新行号
            if self._line_number_update_job:
                self.root.after_cancel(self._line_number_update_job)
            self._line_number_update_job = self.root.after(50, self._redraw_line_numbers)

            # 更新高亮
            if hasattr(self, '_schedule_highlighting'):
                self._schedule_highlighting()
            self.code_text.edit_modified(False) # 重置修改标志

    def on_text_change(self, event=None):
        # 按键释放时，安排行号和高亮更新
        # 更新行号
        if self._line_number_update_job:
            self.root.after_cancel(self._line_number_update_job)
        self._line_number_update_job = self.root.after(100, self._redraw_line_numbers)

        if hasattr(self, '_schedule_highlighting'):
            self._schedule_highlighting() # 更新高亮

    # def print_line_metrics_debug(self):
    #     print("\n--- 开始行度量信息调试 (当前版本代码) ---")
    #     try:
    #         print(f"行号区 (line_numbers_text) 实际字体: {self.line_numbers_text.cget('font')}")
    #         print(f"代码区 (code_text) 实际字体: {self.code_text.cget('font')}")
    #         for i in range(1, 4):
    #             print(f"  行号区 spacing{i}: {self.line_numbers_text.cget(f'spacing{i}')}")
    #             print(f"  代码区 spacing{i}: {self.code_text.cget(f'spacing{i}')}")
    #         print(f"  行号区 padx: {self.line_numbers_text.cget('padx')}, pady: {self.line_numbers_text.cget('pady')}")
    #         print(f"  代码区 padx: {self.code_text.cget('padx')}, pady: {self.code_text.cget('pady')}")
    #         print(f"  行号区 borderwidth: {self.line_numbers_text.cget('borderwidth')}")
    #         print(f"  代码区 borderwidth: {self.code_text.cget('borderwidth')}")
    #     except tk.TclError as e:
    #         print(f"获取 cget 配置时出错: {e}")
    #
    #     for line_num_1_based in range(1, 6):
    #         line_index_tk = f"{line_num_1_based}.0"
    #         ln_bbox_info = "不可用或行不存在"
    #         ct_bbox_info = "不可用或行不存在"
    #         try:
    #             if self.line_numbers_text.compare(line_index_tk, "<", self.line_numbers_text.index("end")):
    #                 bbox = self.line_numbers_text.dlineinfo(line_index_tk)
    #                 if bbox: ln_bbox_info = f"y={bbox[1]}, height={bbox[3]}, baseline={bbox[4]}"
    #         except tk.TclError as e: ln_bbox_info = f"TclError: {e}"
    #         try:
    #             if self.code_text.compare(line_index_tk, "<", self.code_text.index("end")):
    #                 bbox = self.code_text.dlineinfo(line_index_tk)
    #                 if bbox: ct_bbox_info = f"y={bbox[1]}, height={bbox[3]}, baseline={bbox[4]}"
    #         except tk.TclError as e: ct_bbox_info = f"TclError: {e}"
    #         print(f"\n第 {line_num_1_based} 行:")
    #         print(f"  行号区: {ln_bbox_info}")
    #         print(f"  代码区: {ct_bbox_info}")
    #     print("--- 行度量信息调试结束 ---\n")

    def load_file(self, filepath=None):
    # 加载汇编文件到代码编辑区
    # 如果提供了 filepath 参数，则直接加载该文件;否则，弹出文件选择对话框

        chosen_filepath = filepath  # 使用传入的路径（如果存在）

        if chosen_filepath is None: # 如果没有直接提供路径，则打开对话框
            chosen_filepath = filedialog.askopenfilename(
                title="打开汇编文件",
                filetypes=(("汇编文件", "*.asm *.s *.txt"), ("所有文件", "*.*"))
            )

        if chosen_filepath: # 如果得到了一个有效的路径 (无论是传入的还是选择的)
            try:
                with open(chosen_filepath, 'r', encoding='utf-8') as f:
                    self.code_text.delete('1.0', tk.END)
                    self.code_text.insert('1.0', f.read())
                self.code_text.edit_modified(False)
                self.status_label.config(text=f"已加载: {chosen_filepath}")
                self._redraw_line_numbers()

                if hasattr(self, 'apply_syntax_highlighting'): # 如果有语法高亮功能
                    self.apply_syntax_highlighting()
                # # 成功加载并高亮后，可以自动汇编
                # self.assemble_code()

                # # 调试
                # self.print_line_metrics_debug()

            except FileNotFoundError:
                self.status_label.config(text=f"错误: 文件未找到 '{chosen_filepath}'")
            except Exception as e:
                self.status_label.config(text=f"加载文件错误: {e}")
        # else: # 如果取消了文件对话框，或者传入的filepath无效但没有弹窗，则不执行任何操作
        # self.status_label.config(text="加载操作已取消或路径无效")

    def _update_current_line_highlight(self):
        # 更新代码编辑区中当前执行行的高亮
        # 1. 移除旧的高亮
        if self.current_highlighted_tk_line is not None:
            try:
                # Tkinter 行号是 1-based
                line_start = f"{self.current_highlighted_tk_line}.0"
                line_end = f"{self.current_highlighted_tk_line}.end lineend" #确保整行背景
                self.code_text.tag_remove('current_execution_line_tag', line_start, line_end)

            except tk.TclError:
                pass # 如果行不存在或标签移除出错，忽略
        self.current_highlighted_tk_line = None

        # 2. 应用新的高亮
        if not self.simulator.halted and hasattr(self.simulator, 'pc_to_source_line_map') and self.simulator.pc_to_source_line_map:
            current_pc = self.simulator.previous_pccurrent_pc = self.simulator.previous_pc

            if 0 <= current_pc < len(self.simulator.pc_to_source_line_map):
                source_line_num_1_based = self.simulator.pc_to_source_line_map[current_pc]

                if source_line_num_1_based > 0: # 确保是一个有效的源码行号
                    try:
                        line_start_index = f"{source_line_num_1_based}.0"
                        line_end_index = f"{source_line_num_1_based}.end lineend"

                        self.code_text.tag_add('current_execution_line_tag', line_start_index, line_end_index)
                        # self.code_text.see(line_start_index) # 滚动到该行使其可见，但是会抢占控制权
                        self.current_highlighted_tk_line = source_line_num_1_based

                    except tk.TclError as e:
                        print(f"高亮错误: 无法高亮行 {source_line_num_1_based} (PC={current_pc}): {e}")
            # else:
            # print(f"PC {current_pc} 在映射范围之外或映射无效")


    def _update_button_states(self):
        # 根据模拟器和运行状态更新所有控制按钮的可用性
        if self.is_running_continuously: # 正在连续执行
            self.run_btn.config(state=tk.DISABLED)
            self.step_btn.config(state=tk.DISABLED)
            self.assemble_btn.config(state=tk.DISABLED)
            self.load_btn.config(state=tk.DISABLED)
            self.reset_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)

        else: # 已停止、暂停、或未开始
            # 检查是否有已加载的机器码并且模拟器没有因为错误而永久停止
            can_run_or_step = not self.simulator.halted and \
                hasattr(self.simulator, 'machine_code') and \
                self.simulator.machine_code

            self.run_btn.config(state=tk.NORMAL if can_run_or_step else tk.DISABLED)
            self.step_btn.config(state=tk.NORMAL if can_run_or_step else tk.DISABLED)
            self.assemble_btn.config(state=tk.NORMAL)
            self.load_btn.config(state=tk.NORMAL)
            self.reset_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)


    def assemble_code(self):
        self.status_label.config(text="正在汇编...")
        self.root.update_idletasks()
        self.update_line_numbers()
        self.apply_syntax_highlighting() # 汇编前确保高亮

        # 1. 扩展伪指令 (只做一次)
        asm_code = self.code_text.get('1.0', tk.END)
        asm_lines = asm_code.splitlines()

        try:
            expanded_instr, label_map, data_lma_values, source_lines_for_expanded = \
                pse.expand_pseudo_instructions(asm_lines)

        except Exception as e:
            self.status_label.config(text=f"汇编错误 (扩展阶段): {e}")
            return

        # 2. 生成用于输出文件的机器码 (使用 pseudo.py 的 +1 逻辑)
        try:
            resolved_for_file = pse.resolve_labels(expanded_instr, label_map)
            raw_mc_for_file = [pse.assemble_line(line.strip()) for line in resolved_for_file if line.strip()]

            # 格式化并写入文件 (这段来自 pseudo.py 的 if __name__ 块)
            rom_lines = ['_'.join([c[j:j+4] for j in range(0,16,4)]) for c in raw_mc_for_file[:128]]
            while len(rom_lines) < 128: rom_lines.append("0000_0000_0000_0000") # 假设ROM为128

            data_lines = []
            k=0
            while k < len(data_lma_values):
                b1 = data_lma_values[k]; b1_f = f"{format(b1,'08b')[0:4]}_{format(b1,'08b')[4:8]}"
                b2_f = "0000_0000"

                if k + 1 < len(data_lma_values):
                    b2 = data_lma_values[k+1]; b2_f = f"{format(b2,'08b')[0:4]}_{format(b2,'08b')[4:8]}"
                data_lines.append(f"{b1_f}_{b2_f}"); k+=2

            final_output_for_file = rom_lines + data_lines
            pse.write_machine_code_to_file(final_output_for_file, "machine_code_output.txt")
            print("--- 文件 machine_code_output.txt 已使用 pseudo.py 的原始逻辑生成 ---")

        except Exception as e:
            self.status_label.config(text=f"生成输出文件时出错: {e}")
            # 即使文件生成失败，我们仍然可以尝试加载模拟器

        # 3. 加载代码到模拟器
        success, message = self.simulator.load_program_from_source(
            expanded_instr, label_map, data_lma_values, source_lines_for_expanded
        )

        if success:
            # 优先显示模拟器加载成功的消息
            self.status_label.config(text=message)
            self.simulator.halted = False
        else:
            self.status_label.config(text=f"汇编失败: {message}")
            self.simulator.halted = True

        self.update_ui_state()

        
    def go_to_memory_address(self):
        # 跳转到用户在输入框中指定的内存地址
        addr_str = self.mem_addr_entry.get().strip()
        try:
            # 以16进制解析地址
            start_addr = int(addr_str, 16)

            # 确保地址在有效范围内
            if 0 <= start_addr < len(self.simulator.memory):
                self.memory_view_start_addr = start_addr
                self._update_memory_view()
                self.status_label.config(text=f"内存视图已跳转到地址 0x{start_addr:X}")

            else:
                self.status_label.config(text=f"错误: 地址 0x{start_addr:X} 超出内存范围")

        except ValueError:
            self.status_label.config(text=f"错误: 无效的十六进制地址 '{addr_str}'")


    def _on_text_scroll(self, *args):
        # 代码编辑区滚动时，用于更新滚动条位置，并同步行号区滚动
        self.v_scrollbar.set(*args)
        self.line_numbers_text.yview_moveto(args[0]) # 同步行号区的垂直视图

    def _on_scrollbar_yview(self, *args):
        # 滚动条被拖动时，同时滚动代码编辑区和行号区
        self.code_text.yview(*args)
        self.line_numbers_text.yview(*args)

    def _on_unified_mousewheel_scroll(self, event):
        # 统一处理代码区和行号区的鼠标滚轮事件。
        # 该方法会滚动主代码编辑区 self.code_text。
        # 行号区的同步将通过 self.code_text 的 yscrollcommand 触发的 _on_text_scroll 方法完成。        delta_scroll = 0
        if event.num == 4:
            delta_scroll = -1

        elif event.num == 5:
            delta_scroll = 1

        elif hasattr(event, 'delta') and event.delta != 0:
            delta_scroll = -1 * (event.delta // 120)

        if delta_scroll != 0:
            self.code_text.yview_scroll(delta_scroll, "units")

        return "break" # 阻止事件的默认行为


    def update_line_numbers(self, event=None):
        # 更新行号区域的显示
        self.line_numbers_text.config(state='normal') # 允许修改
        self.line_numbers_text.delete('1.0', 'end')   # 清空旧行号

        # 获取代码编辑区的行数
        # 'end-1c' 表示文本末尾减去一个字符（通常是换行符）
        # .split('.')[0] 获取行号部分
        try:
            # last_line_content = self.code_text.get("end-2l", "end-1l") # 获取倒数第二行的内容
            # if not last_line_content.strip(): # 如果倒数第二行是空的，行数可能偏大
            #    lines = int(self.code_text.index('end-2c').split('.')[0]) # 尝试减去一个字符
            # else:
            lines_str = self.code_text.index('end-1c').split('.')[0]
            lines = int(lines_str) if lines_str else 1

            # 如果文本框为空，index('end-1c') 可能是 '1.0'，此时 lines 为 1
            # 如果只有一行无换行，也是 '1.x'
            # 如果最后一行是空行，也应该计算在内，所以 'end-1c' 是正确的
            first_char_of_last_line = self.code_text.get(f"{lines}.0")
            if not self.code_text.get("1.0", "end-1c").strip() and lines == 1 and not first_char_of_last_line: # 完全为空
                lines = 0


        except ValueError:
            lines = 1 # 默认至少有一行，或在空文本时处理

        # print(f"Debug: Number of lines detected: {lines}") # 调试行数

        if lines > 0 :
            line_numbers_string = "\n".join(str(i) for i in range(1, lines + 1))
            self.line_numbers_text.insert('1.0', line_numbers_string)

        # 调整行号区的宽度以适应最大行号的位数
        max_digits = len(str(lines)) if lines > 0 else 1
        self.line_numbers_text.config(width=max_digits + 1) # 加一点padding

        self.line_numbers_text.config(state='disabled') # 禁止编辑
        self._scroll_sync_y() # 确保更新行号后，滚动位置仍然同步


    def _scroll_sync_y(self, event=None):
        # 确保行号区的垂直滚动与代码区一致
        # 当代码区通过键盘、API等方式滚动时，其yscrollcommand会触发 _on_text_scroll
        # _on_text_scroll 已经负责了大部分同步。此函数可用于在其他情况下强制同步。
        top_fraction, _ = self.code_text.yview()
        self.line_numbers_text.yview_moveto(top_fraction)
        # 滚动条的位置也应该被正确设置，这由 _on_text_scroll -> self.v_scrollbar.set() 完成

    def _update_memory_view(self):
        # 更新内存视图，确保每行正确显示一个字节及其对应的十进制值
        if not hasattr(self, 'memory_display_text') or not self.memory_display_text.winfo_exists():
            return

        self.memory_display_text.config(state='normal')
        self.memory_display_text.delete('1.0', 'end')

        start_byte_addr = self.memory_view_start_addr
        if start_byte_addr % 2 != 0:
            start_byte_addr -= 1

        num_bytes_to_show = 128 # 按需调整显示的字节数
        end_byte_addr = min(start_byte_addr + num_bytes_to_show, len(self.simulator.memory) * 2)

        addr_width = 4

        # 循环遍历字节地址
        for current_byte_addr in range(start_byte_addr, end_byte_addr):
            word_addr = current_byte_addr // 2
            byte_offset = current_byte_addr % 2

            word_binary = self.simulator.memory[word_addr]
            byte_binary = ""
            decimal_value = "N/A"
            formatted_byte = "ERR_FORMAT"

            if len(word_binary) == 16:
                # 1. 根据字节偏移，正确提取8位的二进制字节字符串
                byte_binary = word_binary[0:8] if byte_offset == 0 else word_binary[8:16]

                # 2. 基于提取出的8位字节字符串来计算十进制值
                try:
                    # 注意：用 int(byte_binary, 2) 而不是 int(word_binary, 2)
                    decimal_value = int(byte_binary, 2)
                except (ValueError, TypeError):
                    decimal_value = "N/A"

                # 3. 准备格式化的8位二进制显示
                formatted_byte = f"{byte_binary[0:4]}_{byte_binary[4:8]}"

            # 4. 构建包含正确十进制值的显示行
            line = f"0x{current_byte_addr:0{addr_width}X}: {formatted_byte} ({decimal_value})\n"
            self.memory_display_text.insert('end', line)

        self.memory_display_text.config(state='disabled')


    def update_ui_state(self, is_continuous_run=False):
        # 根据模拟器的当前状态更新所有UI元素
        # is_continuous_run: 一个布尔值，用于判断当前是否处于连续执行模式

        # 1. 更新寄存器和PC （开销小，总是更新）
        for i in range(16):
            val = self.simulator.get_reg_value(i)
            self.reg_labels[i].config(text=f"{val} (0x{val:04X})")
        # pc_val = self.simulator.pc
        # self.pc_label_val.config(text=f"{pc_val} (0x{pc_val:04X})")

        # 2. 有条件地更新内存视图
        if not is_continuous_run:
            # 如果是单步执行、暂停、或程序结束时，总是完整刷新内存视图
            if hasattr(self, '_update_memory_view'):
                self._update_memory_view()

        else:
            # 如果是连续执行模式，我们只定期刷新内存视图以提升性能
            self.run_step_counter += 1
            # 20 刷新一次,好像实现,但是祖宗之法不可变
            if self.run_step_counter % 20 == 0:
                if hasattr(self, '_update_memory_view'):
                    self._update_memory_view()

        # 3. 更新按钮状态
        if hasattr(self, '_update_button_states'):
            self._update_button_states()

        # 4. 更新行号区滚动和当前行高亮
        self._scroll_sync_y()
        if hasattr(self, '_update_current_line_highlight'):
            self._update_current_line_highlight()

    def step_code(self):
        if self.simulator.step():
            self.status_label.config(text=f"已单步执行. PC = {self.simulator.pc}")

        else:
            self.status_label.config(text="模拟器已停止")
        self.update_ui_state()

    def run_code(self):
        if self.is_running_continuously: return
        if self.simulator.halted:
            self.status_label.config(text="模拟器已停止，无法连续执行。请重置。")
            return

        self.is_running_continuously = True

        # print(f"--- DEBUG: run_code - 'is_running_continuously' 设置为 {self.is_running_continuously} ---")

        self.status_label.config(text="正在连续执行...")
        self._update_button_states() # 禁用“执行”、“单步”等，启用“停止”
        self._execute_next_instruction_in_run_mode()


    def _execute_next_instruction_in_run_mode(self):
        # print(f"--- DEBUG: 进入 _execute_next... - is_running: {self.is_running_continuously}, halted: {self.simulator.halted} ---")

        # 1. 检查是否应该停止连续执行 (由用户点击停止、模拟器已停止、或断点触发)
        if not self.is_running_continuously or self.simulator.halted:
            self.is_running_continuously = False # 确保标志位正确

            if self._continuous_run_job:
                self.root.after_cancel(self._continuous_run_job)
                self._continuous_run_job = None

            # 更新状态信息和按钮
            # 只有在状态不是由“断点暂停”或“手动停止”设置时，才覆盖状态信息
            current_status = self.status_label.cget("text")
            if "暂停" not in current_status and "停止" not in current_status:
                final_status = "模拟器已停止."

                if self.simulator.halted:
                    # 给出更具体的停止原因
                    is_at_end = False

                    if self.simulator.pc >= len(self.simulator.pc_to_source_line_map):
                        is_at_end = True

                    if is_at_end:
                        final_status = "程序执行完毕."
                    else:
                        final_status = "模拟器因错误或未知原因停止."
                self.status_label.config(text=final_status)

            self._update_button_states() # 更新所有按钮
            self.update_ui_state()       # 更新UI显示（寄存器、PC、高亮等）
            return # 结束本次执行

        # 2.断点检查 (在执行指令之前)
        current_pc = self.simulator.pc
        # 确保 pc_to_source_line_map 已加载且 PC 在有效范围内

        if hasattr(self.simulator, 'pc_to_source_line_map') and \
        self.simulator.pc_to_source_line_map and \
        0 <= current_pc < len(self.simulator.pc_to_source_line_map):

            source_line_num = self.simulator.pc_to_source_line_map[current_pc]
            if source_line_num in self.breakpoints:
                # 命中断点
                self.is_running_continuously = False # 停止连续运行

                # print(f"--- DEBUG: 断点命中! - 'is_running_continuously' 设置为 {self.is_running_continuously} ---")

                self.status_label.config(text=f"在断点处暂停: 第 {source_line_num} 行 (PC={current_pc})")

                self._update_button_states() # 更新按钮状态（启用"单步"、"执行"等）
                self.update_ui_state()       # 刷新UI以高亮断点行

                # 暂停执行，不调用 step() 也不安排下一次 after()
                return
                # 断点检查结束

        # 3. 如果没有命中断点，则执行一步
        # simulator.step() 会执行指令并更新PC。如果执行后出错或结束，它会返回 False。
        if not self.simulator.step():
            self.is_running_continuously = False # 模拟器内部停止了

            # print(f"--- DEBUG: simulator.step() 返回 False - 'is_running_continuously' 设置为 {self.is_running_continuously} ---")

            # 状态将在下一次调用此函数开头的 if 块中被处理和更新
            # 为了立即响应，我们也可以在这里直接处理
            self.status_label.config(text="模拟器执行时遇到错误或结束。")
            self._update_button_states()
            self.update_ui_state()
            return

        # 4. 更新UI并安排下一次执行
        self.update_ui_state() # 更新寄存器、PC、内存、高亮行等

        # 再检查，以防 step() 操作改变了状态 (例如，执行了最后一条指令)
        # print(f"--- DEBUG: 准备安排下一次 after() - is_running: {self.is_running_continuously}, halted: {self.simulator.halted} ---")

        if self.is_running_continuously and not self.simulator.halted:
            delay_ms = 50  # 执行速度控制 (毫秒)
            self._continuous_run_job = self.root.after(delay_ms, self._execute_next_instruction_in_run_mode)
        # else:
        #     print(f"--- DEBUG: 循环终止 - is_running: {self.is_running_continuously}, halted: {self.simulator.halted} ---")

    def stop_continuous_run(self):
        if self.is_running_continuously:
            self.status_label.config(text="已手动停止连续执行.")
        self.is_running_continuously = False

        # print(f"--- DEBUG: stop_continuous_run - 'is_running_continuously' 设置为 {self.is_running_continuously} ---")

        if self._continuous_run_job:
            self.root.after_cancel(self._continuous_run_job)
            self._continuous_run_job = None
        self._update_button_states() # 立即启用“执行”、“单步”等，禁用“停止”

    # 这是之前"内存调试"那个键用的,现在已经没用了
    # def debug_print_memory(self):
    #     # 打印关键内存地址的内容以供调试
    #     print("\n--- 内存状态调试 ---")
    #     if not hasattr(self.simulator, 'memory') or not self.simulator.memory:
    #         print("模拟器内存尚未初始化。")
    #         return
    #
    #     # 检查代码预期的ROM数据地址 (0x0100 对应字地址 128)
    #     expected_data_addr = 128
    #     # 检查之前错误的地址 (0x0200 对应字地址 256)
    #     wrong_data_addr = 256
    #
    #     print(f"模拟器总内存大小: {len(self.simulator.memory)} 字")
    #
    #     if len(self.simulator.memory) > wrong_data_addr + 5: # 确保索引有效
    #         print(f"内存地址 0x{expected_data_addr:04X} (字地址 {expected_data_addr}) 的内容: {self.simulator.memory[expected_data_addr]}")
    #         print(f"内存地址 0x{wrong_data_addr:04X} (字地址 {wrong_data_addr}) 的内容: {self.simulator.memory[wrong_data_addr]}")
    #
    #         # 我们期望看到 self.simulator.memory[128] 的值是 "0000110100001100" (代表13和12)
    #         # 而不是全0
    #     else:
    #         print("内存大小不足，无法执行此调试。")
    #     print("--- 调试结束 ---\n")


    def reset_simulator(self):
        self.is_running_continuously = False # 如果正在运行，则停止
        if self._continuous_run_job:
            self.root.after_cancel(self._continuous_run_job)
            self._continuous_run_job = None

        self.simulator.reset() # Simulator 内部会重置 pc 和 pc_to_source_line_map
        self.status_label.config(text="已重置.")
        # self.pc_to_source_line_map = [] # simulator.reset() 应该处理

        if hasattr(self, 'breakpoints') and isinstance(self.breakpoints, set):
            self.breakpoints.clear()
            # print("--- DEBUG: 所有断点已在重置时清除 ---") # 调试
        else:
            # 如果 breakpoints 属性不存在或类型不正确，创建一个空的，以防后续代码出错
            self.breakpoints = set()

        # 清除旧的高亮，因为PC变为0
        if self.current_highlighted_tk_line is not None:
             try:
                line_start = f"{self.current_highlighted_tk_line}.0"
                line_end = f"{self.current_highlighted_tk_line}.end lineend"
                self.code_text.tag_remove('current_execution_line_tag', line_start, line_end)
             except tk.TclError: pass
        self.current_highlighted_tk_line = None

        self._update_button_states()
        self.update_ui_state() # 会根据 PC=0 重新高亮 (如果映射存在且有效)
        if hasattr(self, '_redraw_line_numbers'): # 确保方法存在
            self._redraw_line_numbers()
        elif hasattr(self, 'update_line_numbers'): # 兼容旧名称
            self.update_line_numbers()

        # 确保停止按钮在重置后也禁用
        self.stop_btn.config(state=tk.DISABLED)
        self.run_btn.config(state=tk.NORMAL) # 重置后应该可以运行
        self.step_btn.config(state=tk.NORMAL) # 重置后应该可以单步

if __name__ == '__main__':

    _original_opcode_map = pse.opcode_map.copy()
    _original_reg_alias = pse.register_alias.copy()
    _original_reg_bin = pse.reg_bin
    _original_imm_bin = pse.imm_bin

    if 'opcode_map' not in globals(): opcode_map = _original_opcode_map
    if 'register_alias' not in globals(): register_alias = _original_reg_alias
    if 'reg_bin' not in globals() or pse.reg_bin.__doc__ is None : reg_bin = _original_reg_bin
    if 'imm_bin' not in globals() or pse.imm_bin.__doc__ is None : imm_bin = _original_imm_bin

    root = tk.Tk()
    app = App(root)
    root.mainloop()