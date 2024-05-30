import utilities.network   as network
import utilities.directory as directory
from utilities.message     import encode_packet,decode_packet
from utilities.log         import log

import threading
import socket
import struct
from time   import sleep
from random import randint

# EVENTS # 
SERVICE_ONLINE = threading.Event() # service status

def play(service):
    # handshake that unjams this endpoint
    # used to sync all endpoints
    try:
        while True:
            header = recv_all(service,4)
            if not header:
                raise Exception("received nothing [header]")
            length = struct.unpack("!I",header)[0]
            data_recv = recv_all(service,length)
            if not data_recv:
                raise Exception("received nothing [body]")
            _,_,msg_flag,_ = decode_packet(data_recv)
            match msg_flag:
                case SYNC if SYNC in ["SYNC"]:
                    log(service,"received SYNC")
                    send(service,0,"SYNC_ACK")
                    return True
                case NSYNC if NSYNC in ["NSYNC"]:
                    log(service,"received NSYNC")
                    continue
                case _:
                    raise Exception(f"SYNC/NSYNC expected yet {msg_flag} received")
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()
        return False
    
def send(service,msg_ID,msg_flag,msg_content=None):
    try:
        if not SERVICE_ONLINE.is_set():
            log(service,f"detected DOWNTIME (send) | service OFFLINE")
            SERVICE_SOCKET.close()
            return False
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_content)
        log(service,f"sending {msg_flag}...")
        length = struct.pack("!I",len(data_encd))
        SERVICE_SOCKET.sendall(length + data_encd)
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME (send) | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()
        return False

def recv_all(service,length):
    try:
        data_read = bytearray()
        while len(data_read) < length:
            chunk = SERVICE_SOCKET.recv(length - len(data_read))
            if not chunk:
                raise Exception("detected DOWNTIME (recv) | received nothing")
            data_read.extend(chunk)
        return bytes(data_read)
    except Exception as e:
        log(service,f"detected DOWNTIME (recv) | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()
        return None

def recv(service,msg_ID,msg_timestamp,msg_flag,msg_content):
    try:
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
                photo_path = directory.PHOTO_DIR + "recv.png"
                with open(photo_path,"wb") as photo_file:
                    photo_file.write(bytes.fromhex(msg_content))
                ...
            case _:
                raise Exception(f"flag={msg_flag} not supported")
    except Exception as e:
        log(service,f"detected DOWNTIME (recv) | caught {e}")
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
            SERVICE_ONLINE.set()
            log(service,f"connection established with {SERVICE_IPV4}")
            play(service) # check bool
            while True:
                if not SERVICE_ONLINE.is_set():
                    log(service,f"detected DOWNTIME - service OFFLINE")
                    SERVICE_SOCKET.close()
                    return
                header = recv_all(service,4)
                if not header:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                length = struct.unpack("!I",header)[0]
                data_recv = recv_all(service,length)
                if not data_recv:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(data_recv)
                log(service,f"received {msg_flag}")
                recv(service,msg_ID,msg_timestamp,msg_flag,msg_content)
        except ConnectionRefusedError:
            log(service,f"connection with {SERVICE_IPV4} refused")
            SERVICE_ONLINE.clear()
    except KeyboardInterrupt:
        log(service,"shutting down...")
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