from utilities.message import message,message_unpack
from utilities.codec   import encode,decode
from utilities.log     import log
from utilities.network import CC_IPV4,MB_PORT
from random            import randint
from time              import sleep
import socket

''' TO DO:
    - new thread for receiving hand
    - clear log polution
    - try catch during handshake
'''

def client():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((CC_IPV4,MB_PORT))
            log("MB-SIM",f"connection established with {CC_IPV4}")
            try:
                data_recv = client_socket.recv(1024)
                data_decd = decode(data_recv)
                msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
                msg_ID = 1
                while True:
                    sleep(5) # wait 5 sec
                    data_flag = ["OPEN_R","CLOSE_R","PHOTO_R"]
                    data_cont = data_flag[randint(0,len(data_flag)-1)]
                    data_send = message(msg_ID,f"{data_cont}")
                    data_encd = encode(data_send)
                    log("MB-SIM",f"sending {data_send}...")
                    client_socket.sendall(data_encd)
                    ####################
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
                    log("MB-SIM",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")
                    ####################
                    msg_ID += 1
            except Exception as e:
                log("MB-SIM",f"error: {e}")
        except ConnectionRefusedError:
            log("MB-SIM",f"connection with {CC_IPV4} refused")
        finally:
            client_socket.close()
    except KeyboardInterrupt:
        log("MB-SIM",f"shutting down...")

def main():
    client()

if __name__ == "__main__": main()