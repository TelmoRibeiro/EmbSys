import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl
from time              import sleep
import socket
import threading

'''
    ATTENTION:
        - I AM AWARE THERE ARE SOME COMMUNICATION BUGS
        - WHEN CONNECTION FAILS WITH SOMEONE ALL THE CONNECTIONS SHOULD BE DROPED
            - AND TRIED AGAIN
        - IF YOU HAVE FEEDBACK IN WAYS I CAN IMRPOVE THE CODE OR
        - IF YOU KNOW OF ANY BUGS
        === HIT ME ON DMs ===
    Telmo Ribeiro
'''

# EVENTS:
MOUSET_EVENT = threading.Event() # used to notify the mouse-trap socket is known
MULTIM_EVENT = threading.Event() # used to notify the multimedia socket is known
MOBILE_EVENT = threading.Event() # used to notify the mobile     socket is known
SENSOR_EVENT = threading.Event() # used to notify the sensor processing function

# blocks communication until every service is live #
# service <=> socket mapping #
def stop(service,client_socket):
    match service:
        case MOBILE_SERVICE if MOBILE_SERVICE == network.MOBILE_SERVER:
            global MOBILE_SOCKET
            MOBILE_SOCKET = client_socket
            MOBILE_EVENT.set()
            while (not MOUSET_EVENT.is_set()) or (not MULTIM_EVENT.is_set()):
                continue
        case MULTIM_SERVICE if MULTIM_SERVICE == network.MULTIM_SERVER:
            global MULTIM_SOCKET
            MULTIM_SOCKET = client_socket
            MULTIM_EVENT.set()
            while (not MOUSET_EVENT.is_set()) or (not MOBILE_EVENT.is_set()):
                continue
        case MOUSET_SERVICE if MOUSET_SERVICE == network.MOUSET_SERVER:
            global MOUSET_SOCKET
            MOUSET_SOCKET = client_socket
            MOUSET_EVENT.set()
            while (not MULTIM_EVENT.is_set()) or (not MOBILE_EVENT.is_set()):
                continue
        case _: raise RuntimeError(f"service={service} not supported!")

# resumes communications after every service is live #
def play(service,client_socket):
    #MOBILE_EVENT.clear()
    #MULTIM_EVENT.clear()
    #MOUSET_EVENT.clear()
    ##########
    _,data_encd = encode_packet(0,"SYNC")
    log_cnsl(service,"sending SYNC...")
    client_socket.sendall(data_encd)
    ##########
    _,_,msg_content = decode_packet(client_socket.recv(1024))
    log_cnsl(service,"received SYNC_ACK!")
    if msg_content != "SYNC_ACK":
        raise RuntimeError(f"SYNC_ACK expected yet {msg_content} received")

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
            stop(service,client_socket) # wait until all services are online
            try:
                play(service,client_socket) # unjams communication
                while True:
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    msg_ID,msg_timestamp,msg_content = decode_packet(data_recv)
                    log_cnsl(service,f"received {msg_content}!")
                    message_control_thread = threading.Thread(target=message_control,args=(service,msg_ID,msg_timestamp,msg_content,))
                    message_control_thread.start()
            except Exception as e:
                log_cnsl(service,f"catched: {e}")
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        log_cnsl(service,"shutting down...")
    finally:
        server_socket.close()      

def message_control(service,msg_ID,msg_timestamp,msg_content):
    # @ telmo - not testing for msg_src...
    match msg_content:
        case FLAG if FLAG in ["OPEN_R","CLOSE_R","PHOTO_R"]:
            client_socket = MOUSET_SOCKET
            if SENSOR_EVENT.is_set() and FLAG != "PHOTO_R":
                SENSOR_EVENT.clear()
            _,data_encd = encode_packet(msg_ID,msg_timestamp,msg_content)
            log_cnsl(service,f"sending {msg_content}...")
            client_socket.sendall(data_encd)
        case FLAG if FLAG in ["OPEN_E","CLOSE_R","PHOTO_E"]:
            client_socket = MOBILE_SOCKET
            _,data_encd = encode_packet(msg_ID,msg_timestamp,msg_content)
            log_cnsl(service,f"sending {msg_content}...")
            client_socket.sendall(data_encd)
        case FLAG if FLAG in ["SENSOR_E"]:
            client_socket = MOBILE_SOCKET
            _,data_encd = encode_packet(msg_ID,msg_timestamp,msg_content)
            log_cnsl(service,f"sending {msg_content}...")
            client_socket.sendall(data_encd)
            SENSOR_EVENT.set()
            sleep(5)
            # @ telmo - what shall happen if SENSOR_E arrives while SENSOR_E is processed?
            if SENSOR_EVENT.is_set():
                client_socket = MOUSET_SOCKET
                _,data_encd = encode_packet(msg_ID,"CLOSE_R")
                log_cnsl(service,f"sending CLOSE_R...")
                client_socket.sendall(data_encd)
            SENSOR_EVENT.clear()
        case _: RuntimeError(f"service={msg_content} not supported!")

def main():
    mobile_thread = threading.Thread(target=server,args=(network.MOBILE_SERVER,))
    multim_thread = threading.Thread(target=server,args=(network.MULTIM_SERVER,))
    mouset_thread = threading.Thread(target=server,args=(network.MOUSET_SERVER,))
    mobile_thread.start()
    multim_thread.start()
    mouset_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()