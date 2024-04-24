import sys
import datetime

def main():
    args_num = len(sys.argv)
    if args_num == 2:
        msg_ID      = sys.argv[0]
        msg_content = sys.argv[1]
        return message(msg_ID,msg_content)
    if args_num == 3:
        msg_ID        = sys.argv[0]
        msg_content   = sys.argv[1]
        msg_timestamp = sys.argv[2]
        return message(msg_ID,msg_content,msg_timestamp)
    raise RuntimeError(f"args_num={args_num} not supported")

def message(ID,content,timestamp=datetime.datetime.now()):
    return f"{ID}@{timestamp}@{content}@"

def message_unpack(msg_data):
    msg_splt = msg_data.split("@")
    msg_ID        = int(msg_splt[0])
    msg_timestamp = msg_splt[1]
    msg_content   = msg_splt[2]
    return msg_ID,msg_timestamp,msg_content

if __name__ == "__main__": main()