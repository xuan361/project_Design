import tkinter as tk
from tkinter import filedialog, scrolledtext, ttk
import re
import pseudo as pse

class Simulator16Bit:
    def __init__(self):
        self.registers = [0] * 16  # r0 to r15
        self.memory = ["0000_0000_0000_0000"] * 512 # Memory for 512 words (16-bit each)
        self.pc = 0
        self.halted = False
        self.machine_code = [] # 在加载到内存之前存储汇编代码
        self.label_map = {}

        # 将 r0 初始化为 0
        self.registers[register_alias['r0']] = 0

    def reset(self):
        self.registers = [0] * 16
        self.pc = 0
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
            # 值为 16 位，因此必要时模拟溢出
            self.registers[reg_idx] = value & 0xFFFF # 确保 16 位
        else:
            self.registers[reg_idx] = 0 # r0 恒 0

    def load_program_from_source(self, asm_lines):
        # 将汇编代码转换为机器码，并将其存储在内部

        try:
            # 1.扩展伪指令
            expanded_instr, self.label_map, data_lma_values = pse.expand_pseudo_instructions(asm_lines)
            # print(f"Expanded: {expanded_instr}")
            # print(f"Labels: {self.label_map}")
            # print(f"DataLMA: {data_lma_values}")


            # 2. 解析标签
            resolved_instr = pse.resolve_labels(expanded_instr, self.label_map)
            # print(f"Resolved: {resolved_instr}")

            # 3.组装 解析的指令行
            raw_machine_code = []
            for line_content in resolved_instr:
                if line_content.strip(): # Ensure not empty
                    bin_code = pse.assemble_line(line_content.strip()) # Returns "XXXXXXXXXXXXXXXX"
                    raw_machine_code.append(bin_code)
            # print(f"Raw MC: {raw_machine_code}")

            # 4. 处理_data_lma值并与指令代码结合
            # 汇编程序会生成扁平的 `final_output_lines`，其中包含指令和数据
            # 指令部分填充为 256 行
            # 目前只使用 raw_machine_code
            # 需要对齐

            self.machine_code = []
            # 格式化和存储指令机器代码
            for i, code in enumerate(raw_machine_code):
                if i < 256: # 最多 256 条指令
                    self.machine_code.append('_'.join([code[j:j+4] for j in range(0, 16, 4)]))

            # 少于 256 条指令，填0
            while len(self.machine_code) < 256:
                self.machine_code.append("0000_0000_0000_0000")

            # 添加 data_lma 值

            temp_formatted_code = []
            for code in raw_machine_code:
                temp_formatted_code.append('_'.join([code[j:j+4] for j in range(0, 16, 4)]))

            instruction_machine_code_formatted = []
            for code in raw_machine_code:
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
        self.memory = ["0000_0000_0000_0000"] * len(self.memory) # 先清除内存
        # 将汇编程序加载到内存中
        for i, code_word in enumerate(self.machine_code):
            if i < len(self.memory):
                self.memory[i] = code_word.replace('_', '') # 存储为原始二进制字符串
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

        #解码并执行单个 16 位指令字（字符串）（需要为每条指令实现逻辑）

        if instruction_word is None or len(instruction_word) != 16:
            self.halted = True
            print(f"Invalid instruction word: {instruction_word} at PC={self.pc}")
            return

        # 从 pseudo.py 导入的 opcode_map

        # (在 __init__ 中存为 self.OPCODE_MAP)
        # 不是，这对吗?等下检查一下？


        # R-type (add,sub,and,or): rs2(4) rs1(4) rd(4) opcode(4) -> instr[0:4] instr[4:8] instr[8:12] instr[12:16]
        # I-type (addi,subi,jalr):imm(4) rs1(4) rd(4) opcode(4) -> instr[0:4] instr[4:8] instr[8:12] instr[12:16]
        # I-type (lb,lw):        imm(4) rs1(4) rd(4) opcode(4) -> instr[0:4] instr[4:8] instr[8:12] instr[12:16]
        # S-type (sb,sw):        rt(4)  rs1(4) imm(4) opcode(4) -> instr[0:4] instr[4:8] instr[8:12] instr[12:16] (rt是源, rs1是基址)
        # SB-type (beq,ble):     rs2(4) rs1(4) imm(4) opcode(4) -> instr[0:4] instr[4:8] instr[8:12] instr[12:16]
        # U-type (lui):          imm(8)        rd(4) opcode(4) -> instr[0:8] instr[8:12] instr[12:16]
        # UJ-type (jal):         imm(8)        rd(4) opcode(4) -> instr[0:8] instr[8:12] instr[12:16]

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
        #二进制补码转换为有符号整数
        val = int(binary_string, 2)
        if (val & (1 << (bits - 1))) != 0: # 若设置了符号位
            val = val - (1 << bits)        # 计算负值
        return val

    def step(self):
        if self.halted:
            print("Cannot step, simulator halted.")
            return False

        if not (0 <= self.pc < len(self.memory) and self.memory[self.pc] != "0000000000000000"): # Halt on all zeros if desired
            # 检查是否超出了加载的机器码或明确停止
            num_meaningful_opcodes = 0
            for op_ in self.machine_code:
                if op_ != "0000_0000_0000_0000":
                    num_meaningful_opcodes +=1
            if self.pc >= num_meaningful_opcodes: # 或 self.pc >= len(self.machine_code)
                print(f"Halted: PC ({self.pc}) reached end of program or zeroed memory.")
                self.halted = True
                return False

        instruction = self.fetch()
        if instruction:
            self.decode_and_execute(instruction)
            self.print_regs() # 用于调试
        else:
            self.halted = True
            print("Halted: Fetch failed or PC out of bounds.")
            return False

    def run_program(self, max_steps=1000): # 添加 max_steps 防无限循环
        print("Running program...")
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
        self.root = root
        self.root.title("自定义ISA的16位RISC单周期CPU")
        self.simulator = Simulator16Bit()

        main_frame = ttk.Frame(root, padding="2")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # --- 代码编辑区和行号区 ---
        # 创建一个框架来容纳行号和代码文本区
        code_area_frame = ttk.Frame(main_frame)
        code_area_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=(0, 5))
        main_frame.columnconfigure(0, weight=3) # 给代码区分配更多权重
        main_frame.rowconfigure(0, weight=1)    # 让代码区可以垂直伸展

        code_area_frame.rowconfigure(1, weight=1) # 让包含行号和文本框的行可以伸展
        code_area_frame.columnconfigure(1, weight=1) # 让代码文本框可以水平伸展

        ttk.Label(code_area_frame, text="汇编代码:").grid(row=0, column=0, columnspan=3, sticky=tk.W, pady=(0,5))

        # 行号区 (tk.Text)
        self.line_numbers_text = tk.Text(code_area_frame, width=4, padx=3, takefocus=0, border=0,
                                         background='lightgrey', state='disabled', wrap='none',
                                          font=('Arial', 12))
        self.line_numbers_text.grid(row=1, column=0, sticky='ns')

        # 代码编辑区 (tk.Text)
        self.code_text = tk.Text(code_area_frame, width=60, height=25, wrap='none', undo=True,
                                 font=('Arial', 12))
        self.code_text.grid(row=1, column=1, sticky='nsew')

        # 垂直滚动条 (tk.Scrollbar)
        self.v_scrollbar = ttk.Scrollbar(code_area_frame, orient="vertical", command=self._on_scrollbar_yview)
        self.v_scrollbar.grid(row=1, column=2, sticky='ns')

        # 关联滚动条和文本区
        self.code_text.config(yscrollcommand=self._on_text_scroll)

        #水平滚动条
        self.h_scrollbar = ttk.Scrollbar(code_area_frame, orient="horizontal", command=self.code_text.xview)
        self.h_scrollbar.grid(row=2, column=1, sticky='ew') # 放置在代码编辑区下方，只作用于代码区

        self.code_text.config(xscrollcommand=self.h_scrollbar.set)

        # 绑定事件用于同步行号和更新
        self.code_text.bind('<KeyRelease>', self.on_text_change)
        self.code_text.bind('<MouseWheel>', self._on_mousewheel_scroll) # For Windows/ некоторых Linux
        self.code_text.bind('<Button-4>', self._on_mousewheel_scroll)   # For Linux scroll up
        self.code_text.bind('<Button-5>', self._on_mousewheel_scroll)   # For Linux scroll down
        # 当文本框内容改变时（例如撤销/重做/粘贴），也需要更新行号
        self.code_text.bind("<<Modified>>", self.on_text_modified)

        # --- 控制按钮和状态栏 (这部分移到 code_area_frame 或 left_pane 下，取决于整体布局) ---
        # 为了简化，我们假设 left_pane 就是 code_area_frame 上方的区域或其自身
        # 如果 left_pane 是 main_frame 的一部分，你需要调整 grid 的 row/column
        # 这里我们把按钮放在 code_area_frame 下方

        controls_frame = ttk.Frame(code_area_frame) # 将按钮放在代码区下方
        controls_frame.grid(row=3, column=0, columnspan=3, sticky=tk.W + tk.E, pady=5)

        self.load_btn = ttk.Button(controls_frame, text="导入文件", command=self.load_file)
        self.load_btn.pack(side=tk.LEFT, padx=2)
        self.assemble_btn = ttk.Button(controls_frame, text="汇编", command=self.assemble_code)
        self.assemble_btn.pack(side=tk.LEFT, padx=2)
        # ... (其他按钮也 pack 到 controls_frame) ...
        self.step_btn = ttk.Button(controls_frame, text="单步", command=self.step_code, state=tk.DISABLED)
        self.step_btn.pack(side=tk.LEFT, padx=2)
        self.run_btn = ttk.Button(controls_frame, text="执行", command=self.run_code, state=tk.DISABLED)
        self.run_btn.pack(side=tk.LEFT, padx=2)
        self.reset_btn = ttk.Button(controls_frame, text="重置", command=self.reset_simulator, state=tk.DISABLED)
        self.reset_btn.pack(side=tk.LEFT, padx=2)

        self.status_label = ttk.Label(code_area_frame, text="已就绪", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5,0))

        # --- 右侧面板：寄存器和内存视图 ---
        right_pane = ttk.Frame(main_frame, padding="0")
        right_pane.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)
        main_frame.columnconfigure(1, weight=1) # 给右侧面板分配权重
        # ... (右侧面板的寄存器和内存视图代码保持不变，确保它们 grid 到 right_pane) ...
        ttk.Label(right_pane, text="寄存器:").grid(row=0, column=0, sticky=tk.W)
        self.reg_labels = {}
        reg_frame = ttk.Frame(right_pane)
        reg_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        for i in range(16):
            reg_name_display = f'r{i}'
            ttk.Label(reg_frame, text=f"{reg_name_display:>3}:").grid(row=i, column=0, sticky=tk.W, padx=2, pady=1)
            self.reg_labels[i] = ttk.Label(reg_frame, text="0 (0x0000)", font=("Arial", 12),width=18, relief=tk.GROOVE, anchor=tk.W)
            self.reg_labels[i].grid(row=i, column=1, sticky=tk.W, padx=2, pady=1)
        self.pc_label_title = ttk.Label(reg_frame, text="PC:")
        self.pc_label_title.grid(row=16, column=0, sticky=tk.W, padx=2, pady=(5,1))
        self.pc_label_val = ttk.Label(reg_frame, text="0 (0x0000)", font=("Arial", 12),width=18, relief=tk.GROOVE, anchor=tk.W)
        self.pc_label_val.grid(row=16, column=1, sticky=tk.W, padx=2, pady=(5,1))
        ttk.Label(right_pane, text="内存视图 (前16字):").grid(row=2, column=0, sticky=tk.W, pady=(10,0))
        self.mem_labels = []
        mem_frame = ttk.Frame(right_pane)
        mem_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        for i in range(16):
            addr_label = ttk.Label(mem_frame, text=f"0x{i:03X}:")
            addr_label.grid(row=i, column=0, sticky=tk.W, padx=2, pady=1)
            val_label = ttk.Label(mem_frame, text="0000_0000_0000_0000", font=("Arial", 12), relief=tk.GROOVE, anchor=tk.W)
            val_label.grid(row=i, column=1, sticky=tk.W, padx=2, pady=1)
            self.mem_labels.append(val_label)


        self._line_number_update_job = None # 用于延迟更新行号
        self.update_ui_state()
        self.update_line_numbers() # 初始加载行号

    def _on_text_scroll(self, *args):
        """当代码编辑区滚动时，用于更新滚动条位置，并同步行号区滚动。"""
        self.v_scrollbar.set(*args) # 更新滚动条
        self.line_numbers_text.yview_moveto(args[0]) # 同步行号区的垂直视图

    def _on_scrollbar_yview(self, *args):
        """当滚动条被拖动时，同时滚动代码编辑区和行号区。"""
        self.code_text.yview(*args)
        self.line_numbers_text.yview(*args)

    def _on_mousewheel_scroll(self, event):
        """处理代码编辑区的鼠标滚轮事件，并同步行号区。"""
        # 对于Windows和一些Linux系统，event.delta通常是120的倍数
        # 对于Linux的Button-4/5，event.num是4或5
        if event.num == 4: # Scroll up on Linux
            self.code_text.yview_scroll(-1, "units")
            self.line_numbers_text.yview_scroll(-1, "units")
        elif event.num == 5: # Scroll down on Linux
            self.code_text.yview_scroll(1, "units")
            self.line_numbers_text.yview_scroll(1, "units")
        elif hasattr(event, 'delta') and event.delta != 0: # For Windows
            scroll_amount = -1 if event.delta > 0 else 1
            self.code_text.yview_scroll(scroll_amount, "units")
            self.line_numbers_text.yview_scroll(scroll_amount, "units")
        return "break" # 阻止事件进一步传播导致可能的双重滚动

    def on_text_modified(self, event=None):
        """当文本框内容被修改时（例如，undo/redo/paste），安排行号更新。"""
        # <<Modified>> 事件会在每次修改后触发，我们需要一个标志来避免不必要的重复更新
        # Text widget的 <<Modified>> 会在每次修改后将自身的 "modified" 标志设为 True
        # 我们可以检查这个标志，并在更新行号后将其重设为 False
        if self.code_text.edit_modified():
            if self._line_number_update_job:
                self.root.after_cancel(self._line_number_update_job)
            self._line_number_update_job = self.root.after(50, self.update_line_numbers) # 稍作延迟
            self.code_text.edit_modified(False) # 重置修改标志

    def on_text_change(self, event=None):
        """按键释放时，安排行号更新 (也用于将来的语法高亮)。"""
        if self._line_number_update_job:
            self.root.after_cancel(self._line_number_update_job)
        # 使用较短延迟或在 on_text_modified 中处理更佳
        self._line_number_update_job = self.root.after(100, self.update_line_numbers)


    def update_line_numbers(self, event=None):
        """更新行号区域的显示。"""
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
        """确保行号区的垂直滚动与代码区一致。"""
        # 当代码区通过键盘、API等方式滚动时，其yscrollcommand会触发 _on_text_scroll
        # _on_text_scroll 已经负责了大部分同步。此函数可用于在其他情况下强制同步。
        top_fraction, _ = self.code_text.yview()
        self.line_numbers_text.yview_moveto(top_fraction)
        # 滚动条的位置也应该被正确设置，这由 _on_text_scroll -> self.v_scrollbar.set() 完成

    def load_file(self):
        filepath = filedialog.askopenfilename(
            title="打开文件",
            filetypes=(("Assembly files", "*.asm *.s *.txt"), ("All files", "*.*"))
        )
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.code_text.delete('1.0', tk.END)
                    self.code_text.insert('1.0', f.read())
                self.code_text.edit_modified(False) # 重置修改标志
                self.status_label.config(text=f"已加载: {filepath}")
                self.update_line_numbers() # <--- 加载文件后更新行号
                # self.apply_syntax_highlighting() # 如果之后添加语法高亮
            except Exception as e:
                self.status_label.config(text=f"加载文件错误: {e}")

    # ... (assemble_code, update_ui_state, step_code, run_code, reset_simulator 方法保持不变) ...
    # 但需要确保它们不会干扰行号的更新和同步逻辑，通常不会。
    def assemble_code(self):
        self.status_label.config(text="正在汇编...")
        self.root.update_idletasks()
        self.update_line_numbers() # 汇编前确保行号最新 (可选)
        asm_code = self.code_text.get('1.0', tk.END)
        asm_lines = asm_code.splitlines()
        success, message = self.simulator.load_program_from_source(asm_lines)
        if success:
            self.status_label.config(text="汇编成功，等待执行")
            self.simulator.halted = False
        else:
            self.status_label.config(text=f"汇编失败: {message}")
            self.simulator.halted = True
        self.update_ui_state()

    def update_ui_state(self): # 确保这个方法被正确调用
        for i in range(16):
            val = self.simulator.get_reg_value(i)
            self.reg_labels[i].config(text=f"{val} (0x{val:04X})")
        pc_val = self.simulator.pc
        self.pc_label_val.config(text=f"{pc_val} (0x{pc_val:04X})")
        for i in range(min(16, len(self.simulator.memory))):
            mem_word_bin = self.simulator.memory[i]
            if len(mem_word_bin) == 16:
                formatted_mem_word = '_'.join([mem_word_bin[j:j+4] for j in range(0, 16, 4)])
                self.mem_labels[i].config(text=formatted_mem_word)
            else:
                self.mem_labels[i].config(text=mem_word_bin)
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
        # 确保行号区的滚动位置在UI更新时也可能需要同步
        self._scroll_sync_y()


    def step_code(self):
        if self.simulator.step():
            self.status_label.config(text=f"已单步执行. PC = {self.simulator.pc}")
        else:
            self.status_label.config(text="模拟器已停止")
        self.update_ui_state()

    def run_code(self):
        self.status_label.config(text="正在连续执行...")
        self.root.update_idletasks()
        self.simulator.run_program(max_steps=20000)
        self.status_label.config(text=f"执行完毕. PC = {self.simulator.pc}. 停止状态: {self.simulator.halted}")
        self.update_ui_state()

    def reset_simulator(self):
        self.simulator.reset()
        self.status_label.config(text="模拟器已重置")
        self.update_ui_state()
        self.update_line_numbers() # 重置后也更新一下行号，以防代码被清空等情况

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