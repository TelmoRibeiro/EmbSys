import datetime

def log_cnsl(agent,content,timestamp=datetime.datetime.now()):
    print (f"@ {agent} [{timestamp}] - {content}")
    return f"@ {agent} [{timestamp}] - {content}"

def log_file(agent,content,timestamp=datetime.datetime.now()):
    # @ telmo - TO DO!
    return f"@ {agent} [{timestamp}] - {content}"