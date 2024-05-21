import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl
from time              import sleep
import socket
import threading

'''
    ATTENTION:
        I AM AWARE THERE ARE SOME COMMUNICATION BUGS
        IF YOU UNCOVER BUGS
        === HIT ME ON DMs ===
    TelmoRibeiro
'''

# EVENTS:
MULTIM_ONLINE = threading.Event() # MULTIM CENTER ONLINE?
MOBILE_ONLINE = threading.Event() # MOBILE CENTER ONLINE?
SENSOR_EVENT  = threading.Event() # SENSOR SMART PROCESSING

def stop(service,client_socket):
    match service:
        case THIS_SERVICE if THIS_SERVICE == network.MOBILE_SERVER:
            global MOBILE_SOCKET
            MOBILE_SOCKET = client_socket
            MOBILE_ONLINE.set()
            while not MULTIM_ONLINE.is_set():
                sleep(1)
                _,data_encd = encode_packet(0,"NSYNC")
                try:
                    log_cnsl(service,"sending NSYNC...")
                    client_socket.sendall(data_encd)
                except Exception as e:
                    log_cnsl(service,f"detected DOWNTIME while sending")
                    MOBILE_ONLINE.clear()
                    client_socket.close()
                    return
        case THIS_SERVICE if THIS_SERVICE == network.MULTIM_SERVER:
            global MULTIM_SOCKET
            MULTIM_SOCKET = client_socket
            MULTIM_ONLINE.set()
            while not MOBILE_ONLINE.is_set():
                sleep(1)
                _,data_encd = encode_packet(0,"NSYNC")
                try:
                    log_cnsl(service,"sending NSYNC...")
                    client_socket.sendall(data_encd)
                except Exception as e:
                    log_cnsl(service,f"detected DOWNTIME while sending")
                    MULTIM_ONLINE.clear()
                    client_socket.close()
                    return
        case _:
            log_cnsl(service,f"service={service} not supported!")
            client_socket.close()
            return

def play(service,client_socket):
    _,data_encd = encode_packet(0,"SYNC")
    try:
        log_cnsl(service,"sending SYNC...")
        client_socket.sendall(data_encd)
    except Exception as e:
        match service:
            case network.MOBILE_SERVER:
                log_cnsl(service,f"detected DOWNTIME while sending")
                MOBILE_ONLINE.clear()
            case network.MULTIM_SERVER:
                log_cnsl(service,f"detected DOWNTIME while sending")
                MULTIM_ONLINE.clear()
            case _:
                log_cnsl(service,f"service={service} not supported!")
        client_socket.close()  
    ##########
    try:
        _,_,msg_content = decode_packet(client_socket.recv(1024))
        log_cnsl(service,"received SYNC_ACK!")
        if msg_content != "SYNC_ACK":
            log_cnsl(service,f"SYNC_ACK expected yet {msg_content} received")
            client_socket.close()
    except Exception as e:
        match service:
            case network.MOBILE_SERVER:
                log_cnsl(service,f"detected DOWNTIME while receiving")
                MOBILE_ONLINE.clear()
            case network.MULTIM_SERVER:
                log_cnsl(service,f"detected DOWNTIME while receiving")
                MULTIM_ONLINE.clear()
            case _:
                log_cnsl(service,f"service={service} not supported!")
        client_socket.close()

def server(service):
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM) # tcp connection
    SERVICE_IPV4  = network.SERVER_IPV4 
    SERVICE_PORT  = network.service_port(service)
    server_socket.bind((SERVICE_IPV4,SERVICE_PORT))
    server_socket.listen()
    log_cnsl(service,"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log_cnsl(service,f"connection established with {client_address}!")
            stop(service,client_socket)
            play(service,client_socket)
            try:
                while True:
                    if not MOBILE_ONLINE.is_set() or not MULTIM_ONLINE.is_set():
                        _,data_encd = encode_packet(-1,"SHUTDOWN")
                        log_cnsl(service,f"sending SHUTDOWN...")
                        client_socket.sendall(data_encd)
                        break
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    msg_ID,msg_timestamp,msg_content = decode_packet(data_recv)
                    log_cnsl(service,f"received {msg_content}!")
                    message_control_thread = threading.Thread(target=message_control,args=(service,msg_ID,msg_timestamp,msg_content,))
                    message_control_thread.start()
            except Exception as e:
                match service:
                    case network.MOBILE_SERVER:
                        log_cnsl(service,f"detected DOWNTIME while receiving")
                        MOBILE_ONLINE.clear()
                    case network.MULTIM_SERVER:
                        log_cnsl(service,f"detected DOWNTIME while receiving")
                        MULTIM_ONLINE.clear()
                    case _:
                        log_cnsl(service,f"service={service} not supported!")
                client_socket.close()
    except KeyboardInterrupt:
        log_cnsl(service,"shutting down...")
    finally:
        server_socket.close()

def message_control(service,msg_ID,msg_timestamp,msg_content):
    # @ telmo - not testing for msg_src...
    match msg_content:
        case FLAG if FLAG in ["OPEN_R","CLOSE_R","PHOTO_R"]:
            client_socket = MULTIM_SOCKET
            if SENSOR_EVENT.is_set() and FLAG != "PHOTO_R":
                SENSOR_EVENT.clear()
            _,data_encd = encode_packet(msg_ID,msg_content,msg_timestamp)
            try:              
                log_cnsl(service,f"sending {msg_content}...")
                client_socket.sendall(data_encd)
            except Exception as e:
                log_cnsl(service,"detected DOWNTIME while sending")
                MULTIM_ONLINE.clear()
                client_socket.close()
        case FLAG if FLAG in ["OPEN_E","CLOSE_E","PHOTO_E"]:
            client_socket = MOBILE_SOCKET
            _,data_encd = encode_packet(msg_ID,msg_content,msg_timestamp)
            try:
                log_cnsl(service,f"sending {msg_content}...")
                client_socket.sendall(data_encd)
            except Exception as e:
                log_cnsl(service,"detected DOWNTIME while sending")
                MOBILE_ONLINE.clear()
                client_socket.close()
        case FLAG if FLAG in ["SENSOR_E"]:
            client_socket = MOBILE_SOCKET
            _,data_encd = encode_packet(msg_ID,msg_content,msg_timestamp)
            try:
                log_cnsl(service,f"sending {msg_content}...")
                client_socket.sendall(data_encd)
                SENSOR_EVENT.set()
                sleep(5)
                # @ telmo - what shall happen if SENSOR_E arrives while SENSOR_E is processed?
                if SENSOR_EVENT.is_set():
                    client_socket = MULTIM_SOCKET
                    _,data_encd = encode_packet(msg_ID,"CLOSE_R")
                    try:
                        log_cnsl(service,f"sending CLOSE_R...")
                        client_socket.sendall(data_encd)
                    except Exception as e:
                        log_cnsl(service,f"detected DOWNTIME while sending")
                        MULTIM_ONLINE.clear()
                        client_socket.close()    
                SENSOR_EVENT.clear()
            except Exception as e:
                log_cnsl(service,"detected DOWNTIME while sending")
                MOBILE_ONLINE.clear()
                client_socket.close()
        case _:
            log_cnsl(service,f"service={msg_content} not supported!")
            client_socket.close()

def main():
    mobile_thread = threading.Thread(target=server,args=(network.MOBILE_SERVER,))
    multim_thread = threading.Thread(target=server,args=(network.MULTIM_SERVER,))
    mobile_thread.start()
    multim_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()