import re
def strip_comments(line):
    return re.split(r'#|//', line)[0].strip()
    # 1. re.split(r'#|//', line)
    # 使用正则表达式将字符串 line 按照 # 或 // 进行分割。
    # re.split(...) 返回的是一个列表，前面是实际代码，后面是注释内容

line = "lb a4, 0(r0)     //a4是外层计数器"
print(strip_comments(line))