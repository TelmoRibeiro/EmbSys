# Mouse Trap Controller     #
# Description:              #
#   mouse trap local brain  #
# by Telmo Ribeiro          #

from Message import message
import socket
import datetime

cc_ipv4 = "127.0.0.1"
cc_port = 2500

def connect():
    messageID = 1
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((cc_ipv4, cc_port))
        print("@ mtc - connection established!")
        data_send = message(messageID,datetime.datetime.now(),"Hello?")
        print(f"@ mtc - sending data = {data_send}...")
        server_socket.sendall(bytes(data_send, "utf-8"))
        data_recv = server_socket.recv(1024).decode("utf-8")
        print(f"@ mtc - received data = {data_recv}!")
        print(f"@ mtc - closing connection...")
        messageID += 1
        server_socket.close()
    return

def main():
    connect()
    return

if __name__ == "__main__": main()