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
    - message 0 & real handshake
    - real thread handover
    - clear log polution
    - try catch during handshake
    - ...
'''

def setup(IPV4,PORT):
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((IPV4,PORT))
    return server_socket

def mobile_server():
    server_socket = setup(CC_IPV4,MB_PORT)
    server_socket.listen()
    log("MB-SRV",f"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log("MB-SRV",f"connection established with {client_address}")
            global MB_SOCKET
            MB_SOCKET = client_socket
            MB_EVENT.set()
            log("MB-SRV",f"waiting on all connections...")
            while (not MTC_EVENT.is_set()) or (not MC_EVENT.is_set()):
                continue
            log("MB-SRV",f"all connections established")
            data_send = message(0,"ON")
            data_encd = encode(data_send)
            log("MB-SRV",f"sending {data_send}...")
            client_socket.sendall(data_encd)
            try:
                while True:
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
                    log("MB-SRV",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")
                    ####################
                    match msg_content:
                        case "OPEN_R":
                            log("MB-SRV",f"handing control to {msg_content} thread...")
                            open_r_thread = threading.Thread(target=open_r_control)
                            open_r_thread.start()
                        case "CLOSE_R":
                            log("MB-SRV",f"handing control to {msg_content} thread...")
                            close_r_thread = threading.Thread(target=close_r_control)
                            close_r_thread.start()
                        case "PHOTO_R":
                            log("MB-SRV",f"handing control to {msg_content} thread...")
                            photo_r_thread = threading.Thread(target=photo_r_control)
                            photo_r_thread.start()
                        case _: raise RuntimeError(f"service for {msg_content} not supported")
                    ####################
                    data_send = message(msg_ID,f"{msg_content}")    
                    data_encd = encode(data_send)
                    log("MB-SRV",f"sending {data_send}...")
                    client_socket.sendall(data_encd)
            except Exception as e:
                log("MB-SRV",f"error: {e}")
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        log("MB-SRV",f"shutting down...")
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

def multimedia_server():
    server_socket = setup(CC_IPV4,MC_PORT)
    server_socket.listen()
    log("MM-SVR",f"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log("MM-SRV",f"connection established with {client_address}")
            global MC_SOCKET
            MC_SOCKET = client_socket
            MC_EVENT.set()
            log("MM-SRV",f"waiting on all connections...")
            while (not MTC_EVENT.is_set()) or (not MB_EVENT.is_set()):
                continue
            log("MM-SRV",f"all connections established")
            data_send = message(0,"ON")
            data_encd = encode(data_send)
            log("MM-SRV",f"sending {data_send}...")
            client_socket.sendall(data_encd)
            try:
                while True:
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
                    log("MM-SRV",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")
                    ####################
                    match msg_content:
                        case "PHOTO_E":
                            log("MM-SRV",f"handing control to {msg_content} thread...")
                            photo_e_thread = threading.Thread(target=photo_e_control)
                            photo_e_thread.start()
                        case _: raise RuntimeError(f"service for {msg_content} not supported")
                    ####################
                    data_send = message(msg_ID,f"{msg_content}")    
                    data_encd = encode(data_send)
                    log("MM-SRV",f"sending {data_send}...")
                    client_socket.sendall(data_encd)
            except Exception as e:
                log("MM-SRV",f"error: {e}")
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        log("MM-SRV",f"shutting down...")
    finally:
        server_socket.close()

def photo_e_control():
    log("PHOTO_E",f"forwarding...")
    # send it to mobile + content

def mouse_trap_server():
    server_socket = setup(CC_IPV4,MTC_PORT)
    server_socket.listen()
    log("MTC-SVR",f"listening...")
    try:
        while True:
            client_socket,client_address = server_socket.accept()
            log("MTC-SRV",f"connection established with {client_address}")
            global MTC_SOCKET
            MTC_SOCKET = client_socket
            MTC_EVENT.set()
            log("MTC-SRV",f"waiting on all connections...")
            while (not MC_EVENT.is_set()) or (not MB_EVENT.is_set()):
                continue
            log("MTC-SRV",f"all connections established")
            data_send = message(0,"ON")
            data_encd = encode(data_send)
            log("MTC-SRV",f"sending {data_send}...")
            client_socket.sendall(data_encd)
            try:
                while True:
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
                    log("MTC-SRV",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")
                    ####################
                    match msg_content:
                        case "OPEN_E":
                            log("MTC-SRV",f"handing control to {msg_content} thread...")
                            open_e_thread = threading.Thread(target=open_e_control)
                            open_e_thread.start()
                        case "CLOSE_E":
                            log("MTC-SRV",f"handing control to {msg_content} thread...")
                            close_e_thread = threading.Thread(target=close_e_control)
                            close_e_thread.start()
                        case "SENSOR_E":
                            log("MTC-SRV",f"handing control to {msg_content} thread...")
                            sensor_e_thread = threading.Thread(target=sensor_e_control)
                            sensor_e_thread.start()
                        case _: raise RuntimeError(f"service for {msg_content} not supported")
                    ####################
                    data_send = message(msg_ID,f"{msg_content}")    
                    data_encd = encode(data_send)
                    log("MTC-SRV",f"sending {data_send}...")
                    client_socket.sendall(data_encd)
            except Exception as e:
                log("MTC-SRV",f"error: {e}")
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        log("MTC-SRV",f"shutting down...")
    finally:
        server_socket.close()

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
    mobile_thread = threading.Thread(target=mobile_server)
    mulmed_thread = threading.Thread(target=multimedia_server)
    moutra_thread = threading.Thread(target=mouse_trap_server)
    mobile_thread.start()
    mulmed_thread.start()
    moutra_thread.start()
    #####################

if __name__ == "__main__": main()