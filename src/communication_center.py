#####################################
#   Any bugs? Any Improvements?     #
#   DM me :)                        #
#####################################

# @ telmo - not handling communication errors yet
# @ telmo - threading not handled yet

from utilities.message import message as message
from utilities.codec   import encode
from utilities.codec   import decode
from utilities.log     import log     as log
import socket
import threading

# NETWORKING:
CC_IPV4 = "127.0.0.1"
CC_PORT = 2500
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


def setup():
    server_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server_socket.bind((CC_IPV4,CC_PORT))
    return server_socket

def server(server_socket):
    log("CC",f"listening...")
    server_socket.listen()
    connection, address = server_socket.accept()
    log("CC",f"connection established with {address}")
    while True:
        data_recv = connection.recv(1024)
        fail_safe(data_recv,address)
        data_decd = decode(data_recv)
        data_splt = data_decd.split("@")
        msg_ID        = int(data_splt[0])
        msg_content   = data_splt[1]
        msg_timestamp = data_splt[2]
        log("CC",f"received ID={msg_ID} | content={msg_content} | timestamp={msg_timestamp}")
        #############################################
        msg_ID += 1
        data_send = message(msg_ID,f"current msg_ID={msg_ID}")
        data_encd = encode(data_send)
        log("CC",f"sending {data_send}...")
        connection.sendall(data_encd)
    raise RuntimeError("fatal error...")

def fail_safe(data_recv,address):
    if not data_recv:
        log("CC",f"{address} stopped sending data!")
        log("CC",f"setting up...")
        return main()
    return None

def main():
    server_socket = setup()
    return server(server_socket)

if __name__ == "__main__": main()