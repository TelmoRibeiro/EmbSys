import utilities.network as network
from utilities.message   import encode_packet,decode_packet
from utilities.log       import log

import threading
import socket
import struct
from time import sleep

# EVENTS:
MULTIM_ONLINE = threading.Event() # multim center status
MOBILE_ONLINE = threading.Event() # mobile center status
SENSOR_EVENT  = threading.Event() # sensor smart processing

def toggleOffline(service):
    # changes service status to OFFLINE
    match service:
        case network.MOBILE_SERVER:
            MOBILE_ONLINE.clear()
        case network.MULTIM_SERVER:
            MULTIM_ONLINE.clear()
        case _:
            log(service,f"service={service} not supported")

def stop(service,client_socket):
    # jams everyone until all endpoints are online
    try:
        match service:
            case MOBILE_SERVER if MOBILE_SERVER == network.MOBILE_SERVER:
                global MOBILE_SOCKET
                MOBILE_SOCKET = client_socket
                MOBILE_ONLINE.set()
                while not MULTIM_ONLINE.is_set():
                    sleep(1)
                    _,data_encd = encode_packet(0,"NSYNC")
                    log(service,"sending NSYNC...")
                    MOBILE_SOCKET.sendall(data_encd)
            case MULTIM_SERVER if MULTIM_SERVER == network.MULTIM_SERVER:
                global MULTIM_SOCKET
                MULTIM_SOCKET = client_socket
                MULTIM_ONLINE.set()
                while not MOBILE_ONLINE.is_set():
                    sleep(1)
                    _,data_encd = encode_packet(0,"NSYNC")
                    log(service,"sending NSYNC...")
                    MULTIM_SOCKET.sendall(data_encd)
            case _:
                log(service,f"service={service} not supported")
                log(service,f"cannot close socket from local view")
                toggleOffline(service)
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        toggleOffline(service)
        client_socket.close()
        return False

def play(service,client_socket):
    service += "-HS"
    try:
        _,data_encd = encode_packet(0,"SYNC")
        log(service,"sending SYNC...")
        client_socket.sendall(data_encd)
        ##########
        data_recv = client_socket.recv(1024)
        if not data_recv:
            log(service,f"received nothing")
            toggleOffline(service)
            client_socket.close()
            return False
        _,_,msg_flag,_ = decode_packet(data_recv)
        log(service,f"received {msg_flag}")
        if msg_flag != "SYNC_ACK":
            log(service,f"SYNC_ACK expected yet {msg_flag} received")
            toggleOffline(service)
            client_socket.close()
            return False
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        toggleOffline(service)
        client_socket.close()
        return False

def send(service,client_socket,msg_ID,msg_flag,msg_content=None):
    try:
        # check if online?
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_content)
        log(service,f"sending {msg_flag}...")
        length = struct.pack("!I",len(data_encd))
        client_socket.sendall(length + data_encd)
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME | {e}")
        toggleOffline(service)
        client_socket.close()
        return False

def recv_all(service,client_socket,length):
    try:
        data_read = bytearray()
        while len(data_read) < length:
            chunk = client_socket.recv(length - len(data_read))
            if not chunk:
                log(service,f"detected DOWNTIME (recv) | received nothing")
                toggleOffline(service)
                client_socket.close()
                return None
            data_read.extend(chunk)
        return bytes(data_read)
    except Exception as e:
        log(service,f"detected DOWNTIME (recv) | caught {e}")
        toggleOffline(service)
        client_socket.close()
        return None

def server(service):
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    SERVICE_IPV4  = network.SERVER_IPV4
    SERVICE_PORT  = network.service_port(service)
    server_socket.bind((SERVICE_IPV4,SERVICE_PORT))
    server_socket.listen()
    log(service,"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log(service,f"connection established with {client_address}")
            if not stop(service,client_socket):
                break
            if not play(service,client_socket):
                break
            while True:
                if not MOBILE_ONLINE.is_set() or not MULTIM_ONLINE.is_set():
                    log(service,f"sending SHUTDOWN...")
                    send(service,client_socket,0,"SHUTDOWN")
                    toggleOffline(service)
                    client_socket.close()
                    break
                header = recv_all(service,client_socket,4)
                if not header:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    toggleOffline(service)
                    client_socket.close()
                    continue
                length = struct.unpack("!I",header)[0]
                data_recv = recv_all(service,client_socket,length)
                if not data_recv:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    toggleOffline(service)
                    client_socket.close()
                    continue
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(data_recv)
                log(service,f"received {msg_flag}")
                message_control_thread = threading.Thread(target=message_control,args=(service,msg_ID,msg_timestamp,msg_flag,msg_content,))
                message_control_thread.start()
    except KeyboardInterrupt:
        log(service,"shutting down...")
    finally:
        server_socket.close()

# @ telmo - not testing for source (not hard to, tho...)
def message_control(service,msg_ID,msg_timestamp,msg_flag,msg_content):
    match msg_flag:
        case FLAG if FLAG in ["OPEN_R","CLOSE_R"]:
            SENSOR_EVENT.clear()
            send(service,MULTIM_SOCKET,msg_ID,msg_flag,msg_content)
        case FLAG if FLAG in ["PHOTO_R"]:
            send(service,MULTIM_SOCKET,msg_ID,msg_flag,msg_content)
        case FLAG if FLAG in ["OPEN_E","CLOSE_E","PHOTO_E"]:
            send(service,MOBILE_SOCKET,msg_ID,msg_flag,msg_content)
        case FLAG if FLAG in ["SENSOR_E"]: # @ telmo - SENSOR_E after SENSOR_E?
            send(service,MOBILE_SOCKET,msg_ID,msg_flag,msg_content)
            send(service,MULTIM_SOCKET,msg_ID,"PHOTO_R")
            SENSOR_EVENT.set()
            sleep(5)
            if SENSOR_EVENT.is_set():
                send(service,MULTIM_SOCKET,msg_ID,"CLOSE_R") 
            SENSOR_EVENT.clear()
        case _:
            log(service,f"flag={msg_flag} not supported")
            log(service,f"cannot close socket from local view")
            toggleOffline(service)

def main():
    mobile_thread = threading.Thread(target=server,args=(network.MOBILE_SERVER,))
    multim_thread = threading.Thread(target=server,args=(network.MULTIM_SERVER,))
    mobile_thread.start()
    multim_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()