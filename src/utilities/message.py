import datetime

def message_packet(ID,flag,content,timestamp=datetime.datetime.now()):
    return f"{ID}@{timestamp}@{flag}@{content}@"

def message_unpack(msg_packet):
    msg_splt = msg_packet.split("@")
    return int(msg_splt[0]),msg_splt[1],msg_splt[2],msg_splt[3]

def encode(msg_packet,format="utf-8"):
    return bytes(msg_packet,format)

def decode(msg_packet,format="utf-8"):
    return msg_packet.decode(format)

def encode_packet(ID,flag,content=None,timestamp=datetime.datetime.now()):
    data_send = message_packet(ID,flag,content,timestamp)
    data_encd = encode(data_send)
    return data_send,data_encd

def decode_packet(data_recv):
    data_decd = decode(data_recv)
    ID,timestamp,flag,content = message_unpack(data_decd)
    return ID,timestamp,flag,content