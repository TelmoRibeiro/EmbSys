from utilities.message import message as message
from utilities.log     import log     as log
from utilities.codec   import encode,decode
from utilities.network import CC_IPV4,CC_PORT
import socket

def client():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((CC_IPV4,CC_PORT))
            log("SIM",f"connection established with {CC_IPV4}")
            msg_ID = 1
            try:
                while True:
                    data_send = message(msg_ID,f"current msg_ID={msg_ID}")
                    data_encd = encode(data_send)
                    log("SIM",f"sending {data_send}...")
                    client_socket.sendall(data_encd)
                    #############################################
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    data_splt = data_decd.split("@")
                    msg_ID        = int(data_splt[0])
                    msg_timestamp = data_splt[1]
                    msg_content   = data_splt[2]
                    log("SIM",f"received ID={msg_ID} | content={msg_content} | timestamp={msg_timestamp}")
                    msg_ID += 1
            except Exception as e:
                log("SIM",f"error: {e}")
        except ConnectionRefusedError:
            log("SIM",f"connection with {CC_IPV4} refused")
        finally:
            client_socket.close()
    except KeyboardInterrupt:
        log("SIM",f"shutting down...")

def main():
    client()

if __name__ == "__main__": main()