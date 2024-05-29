import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl

import threading
import socket
import struct

from random            import randint
from time              import sleep

# EVENTS # 
SERVICE_ONLINE = threading.Event() # SERVICE ONLINE?

def play(service):
    while True:
        _,_,msg_flag,_,_ = decode_packet(SERVICE_SOCKET.recv(1024))    
        match msg_flag:
            case SYNC if SYNC in ["SYNC"]:
                log_cnsl(service,"received SYNC")
                _,data_encd = encode_packet(0,"SYNC_ACK")
                log_cnsl(service,"sending SYNC_ACK...")
                SERVICE_SOCKET.sendall(data_encd)
                return
            case NSYNC if NSYNC in ["NSYNC"]:
                log_cnsl(service,"received NSYNC")
                continue
            case _:
                log_cnsl(service,f"SYNC/NSYNC expected yet {msg_flag} received")
                SERVICE_ONLINE.clear()
                SERVICE_SOCKET.close()
                return
    
def send(service,msg_ID,msg_flag,msg_length=0,msg_content=None):
    try:
        if not SERVICE_ONLINE.is_set():
            log_cnsl(service,f"sending {msg_flag}... service OFFLINE")
            SERVICE_SOCKET.close()
            return
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_length,msg_content)
        log_cnsl(service,f"sending {msg_flag}...")
        length = struct.pack("!I",len(data_encd))
        SERVICE_SOCKET.sendall(length + data_encd)
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def recv_all(service,length):
    try:
        data_read = bytearray()
        while len(data_read) < length:
            chunk = SERVICE_SOCKET.recv(length - len(data_read))
            if not chunk:
                raise Exception("received nothing")
            data_read.extend(chunk)
        return bytes(data_read)
    except Exception as e:
        log_cnsl(service,f"DETECTED DOWNTIME | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def recv(service,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content):
    match msg_flag:
        case "SHUTDOWN":
            SERVICE_ONLINE.clear()
            SERVICE_SOCKET.close()
        case "OPEN_E":
            ...
        case "CLOSE_E":
            ...
        case "SENSOR_E":
            ...
        case "PHOTO_E":
            with open("./pics/recv.jpeg","wb") as photo_file:
                photo_file.write(bytes.fromhex(msg_content))
            ...
        case _:
            log_cnsl(service,f"flag={msg_flag} not supported")
            SERVICE_ONLINE.clear()
            SERVICE_SOCKET.close()

def client(service):
    try:
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        SERVICE_IPV4  = network.SERVER_IPV4
        SERVICE_PORT  = network.service_port(service)
        try:
            client_socket.connect((SERVICE_IPV4,SERVICE_PORT))
            global SERVICE_SOCKET
            SERVICE_SOCKET = client_socket
            log_cnsl(service,f"connection established with {SERVICE_IPV4}")
            play(service)
            SERVICE_ONLINE.set()
            while True:
                if not SERVICE_ONLINE.is_set():
                    SERVICE_SOCKET.close()
                    return
                header = recv_all(service,4)
                if not header:
                    log_cnsl(service,f"received None")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                length = struct.unpack("!I",header)[0]
                data_recv = recv_all(service,length)
                if not data_recv:
                    log_cnsl(service,f"received None")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                msg_ID,msg_timestamp,msg_flag,msg_length,msg_content = decode_packet(data_recv)
                log_cnsl(service,f"received {msg_flag}")
                recv(service,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content)
        except ConnectionRefusedError:
            log_cnsl(service,f"connection with {SERVICE_IPV4} refused")
            SERVICE_ONLINE.clear()
    except KeyboardInterrupt:
        log_cnsl(service,"shutting down...")
        SERVICE_ONLINE.clear()

def yourMainLogic(service):
    while not SERVICE_ONLINE.is_set():
        continue
    msg_ID = 1
    while True:
        if not SERVICE_ONLINE.is_set():
            return
        sleep(3)
        data_buff = ["OPEN_R","CLOSE_R","PHOTO_R"]
        data_flag = data_buff[randint(0,len(data_buff)-1)]
        send(service,msg_ID,data_flag) 
        msg_ID += 1
        # THE REST OF UR CODE #

def main():
    mobile_thread = threading.Thread(target=client,args=(network.MOBILE_CLIENT,))
    urmain_mobile_thread = threading.Thread(target=yourMainLogic,args=(network.MOBILE_CLIENT,))
    mobile_thread.start()
    urmain_mobile_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()