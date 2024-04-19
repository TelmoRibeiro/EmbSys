from utilities.message import message as message
from utilities.codec   import encode
from utilities.codec   import decode
from utilities.log     import log     as log
import socket

# NETWORKING:
CC_IPV4 = "127.0.0.1"
CC_PORT = 2500

def setup():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.connect((CC_IPV4,CC_PORT))
    log("SIM",f"connection established with {CC_IPV4}")
    return server_socket

def client(server_socket):
    msg_ID = 1
    while True:
        data_send = message(msg_ID,f"current msg_ID={msg_ID}")
        data_encd = encode(data_send)
        log("CC",f"sending {data_send}...")
        server_socket.sendall(data_encd)
        #############################################
        data_recv = server_socket.recv(1024)
        fail_safe(data_recv,CC_IPV4)
        data_decd = decode(data_recv)
        data_splt = data_decd.split("@")
        msg_ID        = int(data_splt[0])
        msg_content   = data_splt[1]
        msg_timestamp = data_splt[2]
        log("CC",f"received ID={msg_ID} | content={msg_content} | timestamp={msg_timestamp}")
        msg_ID += 1
    raise RuntimeError("fatal error...")

def fail_safe(data_recv,address):
    if not data_recv:
        log("CC",f"{address} stopped sending data!")
        log("CC",f"setting up...")
        return main()
    return None

def main():
    server_socket = setup()
    return client(server_socket)

if __name__ == "__main__": main()