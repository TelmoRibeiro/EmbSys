import datetime

def log(agent,content,timestamp=datetime.datetime.now()):
    print (f"@ {agent} [{timestamp}] - {content}")
    return f"@ {agent} [{timestamp}] - {content}"