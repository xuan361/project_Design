# python_sender_byte_underscore_format.py
# 从 machineCode.txt 读取指令（格式如 0000_0000_0000_0000），并逐字节发送

import serial
import time
import os

# --- 配置参数 ---
SERIAL_PORT = 'COM7'      # 请修改为您的串口号
BAUD_RATE = 9600          # 波特率
CODE_FILE = 'machineCode.txt' # 机器码文件名

def read_machine_code(filename):
    """从文件中读取二进制机器码（格式如 xxxx_xxxx_xxxx_xxxx），忽略空行和注释"""
    if not os.path.exists(filename):
        print(f"错误: 文件 '{filename}' 不存在。")
        return None
    
    instructions = []
    with open(filename, 'r') as f:
        for line_num, line in enumerate(f, 1):
            original_line = line.strip() # 保留原始行用于可能的错误报告
            line = original_line
            
            # 忽略空行和以'/'或'#'开头的注释行
            if not line or line.startswith('//') or line.startswith('#'):
                continue
            
            # 去掉行内注释 (先去掉行内注释，再处理代码格式)
            code_with_potential_separators = line.split('//')[0].strip()
            code_with_potential_separators = code_with_potential_separators.split('#')[0].strip()
            
            # 去掉下划线 (新增加的步骤)
            code_without_separators = code_with_potential_separators.replace('_', '')
            
            # 验证是否是有效的16位二进制数 (对去掉下划线后的字符串进行验证)
            if len(code_without_separators) == 16 and all(c in '01' for c in code_without_separators):
                instructions.append(code_without_separators) # 存储不含下划线的版本
            else:
                print(f"警告: 在文件 '{filename}' 第 {line_num} 行忽略无效格式或无效二进制码 -> '{original_line}' (处理后为 '{code_without_separators}')")
    
    return instructions

def main():
    machine_code_bin = read_machine_code(CODE_FILE) # 读取的是不含下划线的二进制字符串列表
    if machine_code_bin is None:
        return

    print(f"从 '{CODE_FILE}' 文件中成功读取 {len(machine_code_bin)} 条指令。")

    print(f"尝试连接串口 {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        print(f"打开串口失败: {e}")
        return

    print(f"串口 {SERIAL_PORT} 已打开。")
    time.sleep(0.5)

    try:
        # 1. 发送指令总数 (拆分为两个字节)
        num_instructions = len(machine_code_bin)
        print(f"\n准备发送指令总数: {num_instructions}")
        
        count_lsb = (num_instructions & 0xFF).to_bytes(1, 'little')      # 低八位
        count_msb = ((num_instructions >> 8) & 0xFF).to_bytes(1, 'little')  # 高八位
        
        ser.write(count_lsb)
        print(f"  发送计数的低字节: {count_lsb.hex()}")      # hex()将字节、字符串等转化为十六进制字符串
        # time.sleep(0.1) # 字节间延时
        
        ser.write(count_msb)
        print(f"  发送计数的高字节: {count_msb.hex()}")
        # time.sleep(0.1) # 给FPGA一点时间来处理计数值

        # 2. 逐条发送机器指令 (每条指令拆分为两个字节)
        if num_instructions > 0:
            print("\n准备发送机器指令...")
            # enumerate() 用于同时获取当前索引（i）和内容（instr_bin_str）
            for i, instr_bin_str in enumerate(machine_code_bin): # instr_bin_str 是不含下划线的二进制字符串
                print(f"发送指令 {i+1}/{num_instructions}: {instr_bin_str}") # 打印的是不含下划线的版本
                # 将二进制字符串转换为整数
                value = int(instr_bin_str, 2) 
                
                instr_lsb = (value & 0xFF).to_bytes(1, 'little')
                instr_msb = ((value >> 8) & 0xFF).to_bytes(1, 'little')

                ser.write(instr_lsb)
                print(f"  发送指令的低字节: {instr_lsb.hex()}")
                # time.sleep(0.1) # 字节间延时

                ser.write(instr_msb)
                print(f"  发送指令的高字节: {instr_msb.hex()}")
                # time.sleep(0.1) # 指令间延时

    except Exception as e:
        print(f"通信过程中发生错误: {e}")

    finally:
        print(f"\n--- 所有数据发送完成 ---")
        print("FPGA应已自动熄灭LED。")
        print("现在您可以按下FPGA开发板上的复位/启动按钮来运行CPU。")
        ser.close()
        print(f"串口 {SERIAL_PORT} 已关闭。")

if __name__ == "__main__":
    main()
