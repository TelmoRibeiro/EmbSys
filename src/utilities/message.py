import datetime

def message_packet(msg_flag,msg_content=None,msg_timestamp=datetime.datetime.now()):
    return f"{msg_flag}@{msg_content}@{msg_timestamp}@"

def message_unpack(msg_packet):
    msg_splt = msg_packet.split("@")
    return str(msg_splt[0]),msg_splt[1],msg_splt[2]

def encode(msg_packet,format="utf-8"):
    return bytes(msg_packet,format)

def decode(msg_packet,format="utf-8"):
    return msg_packet.decode(format)

def encode_packet(msg_flag,msg_content=None,msg_timestamp=datetime.datetime.now()):
    data_send = message_packet(msg_flag,msg_content,msg_timestamp)
    data_encd = encode(data_send)
    return data_send,data_encd

def decode_packet(data_recv):
    data_decd = decode(data_recv)
    msg_flag,msg_content,msg_timestamp = message_unpack(data_decd)
    return msg_flag,msg_content,msg_timestamp