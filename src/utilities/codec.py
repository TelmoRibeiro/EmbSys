import sys

def encode(content,format="utf-8"):
    return bytes(content,format)

def decode(content,format="utf-8"):
    return content.decode(format)

if __name__ == "__main__":
    args_num = len(sys.argv)
    if args_num < 2 or args_num > 3:
        raise RuntimeError(f"args_num={args_num} not supported")