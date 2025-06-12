import serial
import binascii

def main():
    # 串口配置
    port = "COM7"  # 请根据实际串口号修改
    baudrate = 9600  # 波特率
    ser = serial.Serial(port, baudrate, timeout=1)

    if not ser.is_open:
        ser.open()

    print("串口调试工具已启动！")
    try:
        while True:
            # 提示用户输入被除数
            dividend = input("请输入被除数（十进制或十六进制，例如 3456 或 0x3edf):")
            if dividend.startswith("0x") or dividend.startswith("0X"):
                dividend = int(dividend, 16)
            else:
                dividend = int(dividend)

            # 提示用户输入除数
            divisor = input("请输入除数（十进制或十六进制，例如 123 或 0x47):")
            if divisor.startswith("0x") or divisor.startswith("0X"):
                divisor = int(divisor, 16)
            else:
                divisor = int(divisor)

            # 将被除数和除数转换为字节并发送到串口
            dividend_bytes = dividend.to_bytes(2, byteorder='big')
            divisor_bytes = divisor.to_bytes(2, byteorder='big')

            ser.write(dividend_bytes)  # 发送被除数
            ser.write(divisor_bytes)  # 发送除数

            # 接收商（4 字节）
            quotient_bytes = ser.read(2)
            quotient = int.from_bytes(quotient_bytes, byteorder='big')

            # 接收余数（4 字节）
            remainder_bytes = ser.read(2)
            remainder = int.from_bytes(remainder_bytes, byteorder='big')

            # 输出结果
            print(f"输入被除数：{hex(dividend)}")
            print(f"输入除数：{hex(divisor)}")
            print(f"商：{hex(quotient)}")
            print(f"余数：{hex(remainder)}")

    except KeyboardInterrupt:
        print("\n退出程序")
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        ser.close()


if __name__ == "__main__":
    main()
