import sys
import datetime

# @ telmo - extend file handling

def main():
    args_num = len(sys.argv)
    if args_num == 2:
        log_agent   = sys.argv[0]
        log_content = sys.argv[1] 
        return log(log_agent,log_content)
    if args_num == 3:
        log_agent     = sys.argv[0]
        log_content   = sys.argv[1]
        log_timestamp = sys.argv[2]
        return log(log_agent,log_content,log_timestamp)
    raise RuntimeError(f"args_num={args_num} not supported")

# @ telmo - instead of printing I could write it on a file
def log(agent,content,timestamp=datetime.datetime.now()):
    print(f"@ {agent} [{timestamp}] - {content}")
    return f"@ {agent} [{timestamp}] - {content}"

if __name__ == "__main__": main()