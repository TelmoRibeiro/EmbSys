#####################################
#   Any bugs? Any Improvements?     #
#   DM me :)                        #
#####################################

from utilities.network import CC_IPV4,MTC_PORT,MC_PORT,MB_PORT
from utilities.codec   import encode,decode
from utilities.log     import log
from utilities.message import message,message_unpack
import socket
import threading

# SOCKETS:
MTC_SOCKET = None
MC_SOCKET  = None
MB_SOCKET  = None

# EVENTS:
MTC_EVENT = threading.Event()
MC_EVENT  = threading.Event()
MB_EVENT  = threading.Event()

''' TO DO:
    - real thread handover
    - no log polution?
'''

def service_port(service):
    match service:
        case "MOBILE-SRVR":
            return MB_PORT
        case "MULTIM-SRVR":
            return MC_PORT
        case "MOUSET-SRVR":
            return MTC_PORT
        case _: raise RuntimeError(f"service={service} not supported!")


def hold_connections(service,client_socket):
    match service:
        case "MOBILE-SRVR":
            global MB_SOCKET
            MB_SOCKET = client_socket
            MB_EVENT.set()
            while (not MTC_EVENT.is_set()) or (not MC_EVENT.is_set()):
                continue
        case "MULTIM-SRVR":
            global MC_SOCKET
            MC_SOCKET = client_socket
            MC_EVENT.set()
            while (not MB_EVENT.is_set()) or (not MTC_EVENT.is_set()):
                continue
        case "MOUSET-SRVR":
            global MTC_SOCKET
            MTC_SOCKET = client_socket
            MTC_EVENT.set()
            while (not MB_EVENT.is_set()) or (not MC_EVENT.is_set()):
                    continue
        case _: raise RuntimeError(f"service={service} not supported!")

def resume_connections(service,client_socket):
    data_send = message(0,"SYNC")
    data_encd = encode(data_send)
    log(f"{service}",f"sending {data_send}...")
    client_socket.sendall(data_encd)
    data_recv = client_socket.recv(1024)
    data_decd = decode(data_recv)
    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
    log(f"{service}",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")
    if msg_ID != 0 or msg_content != "SYNC_ACK":
        raise RuntimeError(f"SYNC failed!")

def server(service):
    SERVICE_PORT = service_port(service)
    # TCP CONNECTION #
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((CC_IPV4,SERVICE_PORT))
    server_socket.listen()
    log(f"{service}",f"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log(f"{service}",f"connection established with {client_address}")
            hold_connections(service,client_socket)
            try:
                resume_connections(service,client_socket)
                while True:
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
                    log(f"{service}",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")
                    ####################
                    match msg_content:
                        case "OPEN_R":
                            log(f"{service}",f"handing control to {msg_content} thread...")
                            open_r_thread = threading.Thread(target=open_r_control)
                            open_r_thread.start()
                        case "CLOSE_R":
                            log(f"{service}",f"handing control to {msg_content} thread...")
                            close_r_thread = threading.Thread(target=close_r_control)
                            close_r_thread.start()
                        case "PHOTO_R":
                            log(f"{service}",f"handing control to {msg_content} thread...")
                            photo_r_thread = threading.Thread(target=photo_r_control)
                            photo_r_thread.start()
                        case "OPEN_E":
                            log(f"{service}",f"handing control to {msg_content} thread...")
                            open_e_thread = threading.Thread(target=open_e_control)
                            open_e_thread.start()
                        case "CLOSE_E":
                            log(f"{service}",f"handing control to {msg_content} thread...")
                            close_e_thread = threading.Thread(target=close_e_control)
                            close_e_thread.start()
                        case "PHOTO_E":
                            log(f"{service}",f"handing control to {msg_content} thread...")
                            photo_e_thread = threading.Thread(target=photo_e_control)
                            photo_e_thread.start()
                        case "SENSOR_E":
                            log(f"{service}",f"handing control to {msg_content} thread...")
                            sensor_e_thread = threading.Thread(target=photo_r_control)
                            sensor_e_thread.start()            
                        case _: raise RuntimeError(f"{msg_content} not supported")
                    ####################
                    data_send = message(msg_ID,f"{msg_content}")    
                    data_encd = encode(data_send)
                    log(f"{service}",f"sending {data_send}...")
                    client_socket.sendall(data_encd)
            except Exception as e:
                log(f"{service}",f"error: {e}")
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        log(f"{service}",f"shutting down...")
    finally:
        server_socket.close()      

def open_r_control():
    log("OPEN_R",f"forwarding...")
    # send it to MTC

def close_r_control():
    log("CLOSE_R",f"forwarding...")
    # send it to MTC

def photo_r_control():
    log("PHOTO_R",f"forwarding...")
    # send it to MTC

def photo_e_control():
    log("PHOTO_E",f"forwarding...")
    # send it to mobile + content

def open_e_control():
    log("OPEN_E",f"forwarding...")
    # send it to mobile

def close_e_control():
    log("CLOSE_E",f"forwarding...")
    # send it to mobile

def sensor_e_control():
    log("SENSOR_E",f"forwarding...")
    # big brain moment

def main():
    mobile_thread = threading.Thread(target=server,args=("MOBILE-SRVR",))
    multim_thread = threading.Thread(target=server,args=("MULTIM-SRVR",))
    mouset_thread = threading.Thread(target=server,args=("MOUSET-SRVR",))
    mobile_thread.start()
    multim_thread.start()
    mouset_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()