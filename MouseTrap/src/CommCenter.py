'''
    Communication Center
    telmoribeiro @ 04/10/24
    broker between:
    => Mouse Trap Agent
    => User Agent
'''

from Message import message
import socket
import datetime
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
PHOTO_C = None # @ telmo - photo content

def log(message):
    # @telmo - i can extend this to log in files
    return print(f"@CC[{datetime.datetime.now()}]: {message}")

def server():
    messageID = 1
    # @telmo - errors not handled yet
    # @telmo - threading not handled yet
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((CC_IPV4, CC_PORT))
    log("listening...")
    server_socket.listen()
    connection, address = server_socket.accept()
    log(f"connection established with {address}")
    while True:
        data_recv = connection.recv(1024).decode("utf-8")
        if not data_recv: return log(f"connection with {address} ended!")
        log(f"received data = {data_recv}")
        data_send = message(messageID,datetime.datetime.now(),"HelloWorld!")
        log(f"sending data = {data_send}...")
        connection.sendall(bytes(data_send, "utf-8"))
        messageID += 1
    return

def main():
    return server()

if __name__ == "__main__": main()