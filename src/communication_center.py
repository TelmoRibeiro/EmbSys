#####################################
#   Any bugs? Any Improvements?     #
#   DM me :)                        #
#####################################

from utilities.message import message as message
from utilities.log     import log     as log
from utilities.codec   import encode,decode
from utilities.network import CC_IPV4,CC_PORT
import socket
import threading
import time

# REQUESTS:
OPEN_R  = False
CLOSE_R = False 
PHOTO_R = False
# EVENTS:
OPEN_E   = False
CLOSE_E  = False
PHOTO_E  = False
SENSOR_E = False
# ADITIONAL:
PHOTO_C = None


'''
[...]
if 
'''


def setup():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((CC_IPV4,CC_PORT))
    return server_socket

def server(server_socket):
    server_socket.listen()
    log("CC-SERVER",f"listening...")
    try:
        while True:
            client_socket, client_address = server_socket.accept()
            log("CC-SERVER",f"connection established with {client_address}")
            try:
                while True:
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    data_splt = data_decd.split("@")
                    msg_ID        = int(data_splt[0])
                    msg_timestamp = data_splt[1]
                    msg_content   = data_splt[2]
                    log("CC-SERVER",f"received ID={msg_ID} | content={msg_content} | timestamp={msg_timestamp}")
                    ####################
                    if msg_content == "OPEN_R":
                        log("CC-SERVER",f"handing control to {msg_content} thread...")
                        open_r_thread = threading.Thread(target=open_r_control)
                        open_r_thread.start()
                    elif msg_content == "CLOSE_R":
                        log("CC-SERVER",f"handing control to {msg_content} thread...")
                        close_r_thread = threading.Thread(target=close_r_control)
                        close_r_thread.start()
                    elif msg_content == "PHOTO_R":
                        log("CC-SERVER",f"handing control to {msg_content} thread...")
                        photo_r_thread = threading.Thread(target=photo_r_control)
                        photo_r_thread.start()
                    elif msg_content == "OPEN_E":
                        log("CC-SERVER",f"handing control to {msg_content} thread...")
                        open_e_thread = threading.Thread(target=open_e_control)
                        open_e_thread.start()
                    elif msg_content == "CLOSE_E":
                        log("CC-SERVER",f"handing control to {msg_content} thread...")
                        close_e_thread = threading.Thread(target=close_e_control)
                        close_e_thread.start()
                    elif msg_content == "PHOTO_E":
                        log("CC-SERVER",f"handing control to {msg_content} thread...")
                        photo_e_thread = threading.Thread(target=photo_e_control)
                        photo_e_thread.start()
                    elif msg_content == "SENSOR_E":
                        log("CC-SERVER",f"handing control to {msg_content} thread...")
                        sensor_e_thread = threading.Thread(target=sensor_e_control)
                        sensor_e_thread.start()
                    else:
                        raise RuntimeError("oops unexpected content!")
                    ####################
                    data_send = message(msg_ID,f"{msg_content}")    
                    data_encd = encode(data_send)
                    log("CC-SERVER",f"sending {data_send}...")
                    client_socket.sendall(data_encd)
            except Exception as e:
                log("CC-SERVER",f"error: {e}")
            finally:
                client_socket.close()
    except KeyboardInterrupt:
        log("CC-SERVER",f"shutting down...")
    finally:
        server_socket.close()

def open_r_control():
    log("CC-OPENR",f"opening gates!")

def close_r_control():
    log("CC-CLOSER",f"closing gates!")

def photo_r_control():
    log("CC-PHOTOR",f"asking for photo!")

def open_e_control():
    log("CC-OPENE",f"door was opened!")

def close_e_control():
    log("CC-CLOSEE",f"door was closed!")

def photo_e_control():
    log("CC-PHOTOE",f"photo attached!")

def sensor_e_control():
    log("CC-SENSORE",f"something in the box!")

def main():
    server_socket = setup()
    server_thread = threading.Thread(target=server,args=(server_socket,))
    server_thread.start()
    #####################

if __name__ == "__main__": main()