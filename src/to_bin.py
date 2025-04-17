def to_bin(val, bits):
    if val < 0:
        val = (1 << bits) + val
    return format(val, f"0{bits}b")[-bits:]


print(to_bin(-4,4))