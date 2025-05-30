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

        # 从 pseudo.py 导入的 opcode_map (在 __init__ 中存为 self.OPCODE_MAP)

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
        self.root.title("16-bit ISA Simulator")
        self.simulator = Simulator16Bit()

        # 主框架
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
            reg_name = pse.reg_num_to_name.get(i, f'r{i}')
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
    _original_opcode_map = pse.opcode_map.copy()
    _original_reg_alias = pse.register_alias.copy()
    _original_reg_bin = pse.reg_bin
    _original_imm_bin = pse.imm_bin

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
    if 'reg_bin' not in globals() or pse.reg_bin.__doc__ is None : reg_bin = _original_reg_bin # approx check
    if 'imm_bin' not in globals() or pse.imm_bin.__doc__ is None : imm_bin = _original_imm_bin


    root = tk.Tk()
    app = App(root)
    root.mainloop()