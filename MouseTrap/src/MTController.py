# Mouse Trap Controller     #
# Description:              #
#   mouse trap local brain  #
# by Telmo Ribeiro          #

import socket

cc_ipv4 = "127.0.0.1"
cc_port = 2500

def connect():    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.connect((cc_ipv4, cc_port))
        print("@ mtc - connection established!")
        data = "Hello Word!"
        print(f"@ mtc - sending data = {data}...")
        server_socket.sendall(bytes(data, "UTF-8"))
        data = server_socket.recv(1024)
        print(f"@ mtc - received data = {data}!")
        print(f"@ mtc - closing connection...")
        server_socket.close()
    return

def main():
    connect()
    return

if __name__ == "__main__": main()