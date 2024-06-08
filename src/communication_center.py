import utilities.network as network
from utilities.message   import encode_packet,decode_packet
from utilities.log       import log

from threading import Thread,Event
from struct    import pack,unpack
from time      import sleep

import socket # enables communication with peers

# NETWORK:
SERVICE_IPV4 = network.SERVER_IPV4

# STATUS:
DOOR_STATUS = "OPEN_R"

# EVENTS:
MULTIM_ONLINE = Event() # multim center status
MOBILE_ONLINE = Event() # mobile center status
SENSOR_EVENT  = Event() # sensor smart processing

def server(service):
    # main functionality
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    SERVICE_PORT  = network.service_port(service)
    server_socket.bind((SERVICE_IPV4,SERVICE_PORT))
    server_socket.listen()
    log(service,"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log(service,f"connection established with {client_address}")
            boolS = stop(service,client_socket)
            boolP = play(service,client_socket)
            if not (boolS and boolP):
                toggleOffline(service)
                toggleClose(service)
            try:
                while True:
                    if not MOBILE_ONLINE.is_set() or not MULTIM_ONLINE.is_set():
                        send(service,client_socket,"SHUTDOWN")
                        toggleOffline(service)
                        toggleClose(service)
                        break
                    header = recv_all(service,client_socket,4)
                    if not header:
                        raise Exception("received nothing [header]")
                    length = unpack("!I",header)[0]
                    data_recv = recv_all(service,client_socket,length)
                    # log(service,f"received (RAW) {data_recv}")
                    if not data_recv:
                        raise Exception("received nothing [body]")
                    msg_flag,msg_content,_ = decode_packet(data_recv)
                    log(service,f"received {msg_flag}")
                    message_control_thread = Thread(target=message_control,args=(service,msg_flag,msg_content,))
                    message_control_thread.start()
            except Exception as e:
                log(service,f"detected DOWNTIME | caught {e}")
                toggleOffline(service)
                toggleClose(service)
    except KeyboardInterrupt:
        log(service,"shutting down...")
    finally:
        server_socket.close()

def message_control(service,msg_flag,msg_content):
    # controls the expected behaviour according to the received message
    try:
        match msg_flag:
            case FLAG if FLAG in ["OPEN_R","CLOSE_R"]:
                SENSOR_EVENT.clear()
                send(service,MULTIM_SOCKET,msg_flag,msg_content)
            case FLAG if FLAG in ["PHOTO_R"]:
                send(service,MULTIM_SOCKET,msg_flag,msg_content)
            case FLAG if FLAG in ["OPEN_E","CLOSE_E","PHOTO_E"]:
                if FLAG != "PHOTO_E":
                    global DOOR_STATUS
                    DOOR_STATUS = FLAG
                send(service,MOBILE_SOCKET,msg_flag,msg_content)
            case FLAG if FLAG in ["SENSOR_E"]: # @ telmo - SENSOR_E after SENSOR_E?
                send(service,MOBILE_SOCKET,msg_flag,msg_content)
                send(service,MULTIM_SOCKET,"PHOTO_R")
                SENSOR_EVENT.set()
                sleep(5)
                if SENSOR_EVENT.is_set():
                    send(service,MULTIM_SOCKET,"CLOSE_R")
                SENSOR_EVENT.clear()
            case _:
                raise Exception(service,f"flag={msg_flag} not supported")
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        toggleOffline(service)
        toggleClose(service)

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
                    send(service,MOBILE_SOCKET,"NSYNC")
            case MULTIM_SERVER if MULTIM_SERVER == network.MULTIM_SERVER:
                global MULTIM_SOCKET
                MULTIM_SOCKET = client_socket
                MULTIM_ONLINE.set()
                while not MOBILE_ONLINE.is_set():
                    sleep(1)
                    send(service,MULTIM_SOCKET,"NSYNC")
            case _:
                raise Exception(f"service={service} not supported")
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        toggleOffline(service)
        toggleClose(service)
        return False

def play(service,client_socket):
    # handshake that unjams this endpoint
    # used to sync all endpoints
    try:
        send(service,client_socket,"SYNC",DOOR_STATUS)
        ########## SYNC
        header = recv_all(service,client_socket,4)
        if not header:
            raise Exception("received nothing [header]")
        length = unpack("!I",header)[0]
        data_recv = recv_all(service,client_socket,length)
        if not data_recv:
            raise Exception("received nothing [body]")
        msg_flag,_,_ = decode_packet(data_recv)
        log(service,f"received {msg_flag}")
        if msg_flag != "SYNC_ACK":
            raise Exception(f"SYNC_ACK expected yet {msg_flag} received")
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        toggleOffline(service)
        toggleClose(service)
        return False

def send(service,client_socket,msg_flag,msg_content=None):
    # sends a message through the provided socket
    # it encodes said message before sending
    try:
        _,data_encd = encode_packet(msg_flag,msg_content)
        log(service,f"sending {msg_flag}...")
        length = pack("!I",len(data_encd))
        client_socket.sendall(length + data_encd)
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME (send) | caught {e}")
        toggleOffline(service)
        toggleClose(service)
        return False

def recv_all(service,client_socket,length):
    # revieves messages from the provided socket
    # utilizes length in order to read just the necessary
    try:
        data_read = bytearray()
        while len(data_read) < length:
            chunk = client_socket.recv(length - len(data_read))
            if not chunk:
                raise Exception("detected DOWNTIME (recv) | received nothing")
            data_read.extend(chunk)
        return bytes(data_read)
    except Exception as e:
        log(service,f"detected DOWNTIME (recv) | caught {e}")
        toggleOffline(service)
        toggleClose(service)
        return None

def toggleOffline(service):
    # changes service status to OFFLINE
    match service:
        case network.MOBILE_SERVER:
            MOBILE_ONLINE.clear()
        case network.MULTIM_SERVER:
            MULTIM_ONLINE.clear()
        case _:
            log(service,f"service={service} not supported")

def toggleClose(service):
    # closes communication socket
    match service:
        case network.MOBILE_SERVER:
            MOBILE_SOCKET.close()
        case network.MULTIM_SERVER:
            MULTIM_SOCKET.close()
        case _:
            log(service,f"service={service} not supported")

def main():
    from sys import argv
    if len(argv) == 2:
        global SERVICE_IPV4
        SERVICE_IPV4 = argv[1]
    mobile_thread = Thread(target=server,args=(network.MOBILE_SERVER,))
    multim_thread = Thread(target=server,args=(network.MULTIM_SERVER,))
    mobile_thread.start()
    multim_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()