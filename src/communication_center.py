import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl
from time              import sleep

import threading
import socket
import struct

# EVENTS:
MULTIM_ONLINE = threading.Event() # MULTIM CENTER ONLINE?
MOBILE_ONLINE = threading.Event() # MOBILE CENTER ONLINE?
SENSOR_EVENT  = threading.Event() # SENSOR SMART PROCESSING

def toggleOffline(service):
    match service:
        case network.MOBILE_SERVER:
            MOBILE_ONLINE.clear()
        case network.MULTIM_SERVER:
            MULTIM_ONLINE.clear()
        case _:
            log_cnsl(service,f"service={service} not supported")

def stop(service,client_socket):
    try:
        match service:
            case MOBILE_SERVER if MOBILE_SERVER == network.MOBILE_SERVER:
                global MOBILE_SOCKET
                MOBILE_SOCKET = client_socket
                MOBILE_ONLINE.set()
                while not MULTIM_ONLINE.is_set():
                    sleep(1)
                    _,data_encd = encode_packet(0,"NSYNC")
                    log_cnsl(service,"sending NSYNC...")
                    client_socket.sendall(data_encd)
            case MULTIM_SERVER if MULTIM_SERVER == network.MULTIM_SERVER:
                global MULTIM_SOCKET
                MULTIM_SOCKET = client_socket
                MULTIM_ONLINE.set()
                while not MOBILE_ONLINE.is_set():
                    sleep(1)
                    _,data_encd = encode_packet(0,"NSYNC")
                    log_cnsl(service,"sending NSYNC...")
                    client_socket.sendall(data_encd)
            case _:
                log_cnsl(service,f"service={service} not supported")
                toggleOffline(service)
                client_socket.close()
    except Exception as e:
                    log_cnsl(service,f"detected DOWNTIME | {e}")
                    toggleOffline(service)
                    client_socket.close()

def play(service,client_socket):
    try:
        _,data_encd = encode_packet(0,"SYNC")
        log_cnsl(service,"sending SYNC...")
        client_socket.sendall(data_encd) 
        ##########
        _,_,msg_flag,_,_ = decode_packet(client_socket.recv(1024))
        log_cnsl(service,"received SYNC_ACK!")
        if msg_flag != "SYNC_ACK":
            log_cnsl(service,f"SYNC_ACK expected yet {msg_flag} received")
            toggleOffline(service)
            client_socket.close()
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        toggleOffline(service)
        client_socket.close()

def recv_all(client_socket,length):
    data_read = bytearray()
    while len(data_read) < length:
        chunk = client_socket.recv(length - len(data_read))
        if not chunk:
            raise Exception("received nothing")
        data_read.extend(chunk)
    return bytes(data_read)   

def server(service):
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    SERVICE_IPV4  = network.SERVER_IPV4
    SERVICE_PORT  = network.service_port(service)
    server_socket.bind((SERVICE_IPV4,SERVICE_PORT))
    server_socket.listen()
    log_cnsl(service,"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log_cnsl(service,f"connection established with {client_address}")
            stop(service,client_socket)
            play(service,client_socket)
            try:
                while True:
                    if not MOBILE_ONLINE.is_set() or not MULTIM_ONLINE.is_set():
                        _,data_encd = encode_packet(-1,"SHUTDOWN")
                        log_cnsl(service,f"sending SHUTDOWN...")
                        client_socket.sendall(data_encd)
                        toggleOffline(service)
                        client_socket.close()
                        break
                    header = recv_all(client_socket,4)
                    data_length = struct.unpack("!I",header)[0]
                    data_recv = recv_all(client_socket,data_length)
                    # data_recv = client_socket.recv(1024)
                    if not data_recv:
                        log_cnsl(service,f"received None")
                        toggleOffline(service)
                        client_socket.close()
                        break
                    msg_ID,msg_timestamp,msg_flag,msg_length,msg_content = decode_packet(data_recv)
                    log_cnsl(service,f"received {msg_flag}")
                    message_control_thread = threading.Thread(target=message_control,args=(service,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content,))
                    message_control_thread.start()
            except Exception as e:
                log_cnsl(service,f"detected DOWNTIME | {e}")
                toggleOffline(service)
                client_socket.close()
    except KeyboardInterrupt:
        log_cnsl(service,"shutting down...")
    finally:
        server_socket.close()

def send(service,client_socket,msg_ID,msg_flag,msg_length=0,msg_content=None):
    try:
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_length,msg_content)
        log_cnsl(service,f"sending {msg_flag}...")
        packet_length = struct.pack("!I",len(data_encd)) # testing
        client_socket.sendall(packet_length + data_encd) # testing
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        toggleOffline(service)
        client_socket.close()

# @ telmo - not testing for source (not hard to, tho...)
def message_control(service,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content):
    match msg_flag:
        case FLAG if FLAG in ["OPEN_R","CLOSE_R","PHOTO_R"]:
            if SENSOR_EVENT.is_set() and FLAG in ["OPEN_R","CLOSE_R"]:
                SENSOR_EVENT.clear()
            send(service,MULTIM_SOCKET,msg_ID,msg_flag,msg_length,msg_content)
        case FLAG if FLAG in ["PHOTO_E"]:
            send(service,MOBILE_SOCKET,msg_ID,msg_flag,msg_length,msg_content)
        case FLAG if FLAG in ["OPEN_E","CLOSE_E"]:
            send(service,MOBILE_SOCKET,msg_ID,msg_flag,msg_length,msg_content)
        case FLAG if FLAG in ["SENSOR_E"]:
            send(service,MOBILE_SOCKET,msg_ID,msg_flag,msg_length,msg_content)    
            SENSOR_EVENT.set()
            sleep(5)
            # @ telmo - SENSOR_E after SENSOR_E? - think about it!
            if SENSOR_EVENT.is_set():
                send(service,MULTIM_SOCKET,msg_flag,"CLOSE_R") 
            SENSOR_EVENT.clear()
        case _:
            log_cnsl(service,f"service={msg_flag} not supported")
            log_cnsl(service,f"cannot close at local level")

def main():
    mobile_thread = threading.Thread(target=server,args=(network.MOBILE_SERVER,))
    multim_thread = threading.Thread(target=server,args=(network.MULTIM_SERVER,))
    mobile_thread.start()
    multim_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()