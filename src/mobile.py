import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl
from time              import sleep
from random            import randint
import socket
import threading
from PIL import Image
import numpy

'''
    ATTENTION:
        THERE ARE PLENTY OPTIMISATIONS YOU CAN PERFORM ON THE CODE
        THERE ARE SOME "MANDATORY" SECTIONS IN THE FOLLOWING IMPLEMENTATION THAT ARE NOT INDEED "MANDATORY"
        MANY DESIGN CHOICES WERE MADE TO HAVE A NEET DUALITY CONCEPT BETWEEN THE CLIENT AND THE SERVER
            IF YOU ARE INTERESTED IN OPTIMISING SOME CODE OR
            IF YOU ARE ARE INTERESTED IN DODGING "MANDATORY" PARTS OR
            IF YOU HAVE FEEDBACK IN WAYS I CAN IMPROVE THE CODE
            === HIT ME ON DMs ===
    TelmoRibeiro
'''

# EVENTS # 
SERVICE_ONLINE = threading.Event() # SERVICE ONLINE?
RECV_BYTES    = 1024*1000000

def play(service,client_socket):
    try:
        while True:
            _,_,msg_flag,_ = decode_packet(client_socket.recv(1024))    
            if msg_flag != "SYNC" and msg_flag != "NSYNC":
                log_cnsl(service,f"SYNC/NSYNC expected yet {msg_flag} received!")
                SERVICE_ONLINE.clear()
                client_socket.close()
                return
            if msg_flag == "NSYNC":
                log_cnsl(service,f"received NSYNC")
                continue
            log_cnsl(service,f"received SYNC")
            break
        ##########
        _,data_encd = encode_packet(0,"SYNC_ACK")
        log_cnsl(service,f"sending SYNC_ACK...")
        client_socket.sendall(data_encd)
    except Exception as e:
        log_cnsl(service,f"caught: {e}")
        log_cnsl(service,f"detected DOWNTIME")
        SERVICE_ONLINE.clear()
        client_socket.close()

# call this function whenever you want to send data as long as play event is set #
def send(service,client_socket,msg_ID,msg_flag):
    try:
        if not SERVICE_ONLINE.is_set():
            log_cnsl(service,f"NO CONNECTION!")
            client_socket.close()
            return
        _,data_encd = encode_packet(msg_ID,msg_flag)
        log_cnsl(service,f"sending {msg_flag}...")
        client_socket.sendall(data_encd)
    except Exception as e:
        log_cnsl(service,f"caught: {e}")
        log_cnsl(service,f"detected DOWNTIME")
        SERVICE_ONLINE.clear()
        client_socket.close()

# modify this function to pattern match and treat what you will receive #
def recv(service,msg_ID,msg_timestamp,msg_flag,msg_content):
    # @ telmo - for simulation purpose I will just log it
    match msg_flag:
        case "SHUTDOWN":
            log_cnsl(service,f"received SHUTDOWN")
            SERVICE_ONLINE.clear()
        case "PHOTO_E":
            log_cnsl(service,f"received {msg_flag}")
            print(f"pic: {len(msg_content)}")
            image = Image.frombytes("RGB",(600,600),msg_content,"raw")
            image.show()
        case _: log_cnsl(service,f"received {msg_flag}")

def client(service):
    try:
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        SERVICE_IPV4  = network.SERVER_IPV4
        SERVICE_PORT  = network.service_port(service)
        try:
            client_socket.connect((SERVICE_IPV4,SERVICE_PORT))
            log_cnsl(service,f"connection established with {SERVICE_IPV4}!")
            global SERVICE_SOCKET
            SERVICE_SOCKET = client_socket
            play(service,client_socket)
            SERVICE_ONLINE.set()
            try:
                while True:
                    if not SERVICE_ONLINE.is_set():
                        return
                    data_recv = client_socket.recv(RECV_BYTES)
                    if not data_recv:
                        log_cnsl(service,"nothing received")
                        SERVICE_ONLINE.clear()
                        client_socket.close()
                        break
                    msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(data_recv)
                    recv(service,msg_ID,msg_timestamp,msg_flag,msg_content)
            except Exception as e:
                log_cnsl(service,f"caught: {e}")
                log_cnsl(service,f"detected DOWNTIME")
                SERVICE_ONLINE.clear()
                client_socket.close()
        except ConnectionRefusedError:
            log_cnsl(service,f"connection with {SERVICE_IPV4} refused")
            SERVICE_ONLINE.clear()
            client_socket.close()
    except KeyboardInterrupt:
        log_cnsl(service,"shutting down...")
        SERVICE_ONLINE.clear()

def yourMainLogic(service):
    while not SERVICE_ONLINE.is_set():
        continue
    client_socket = SERVICE_SOCKET
    msg_ID = 1
    while True:
        if not SERVICE_ONLINE.is_set():
            return
        # @ telmo - for simulation purpose I will sleep 3 seconds and then call a random flag
        sleep(3)
        data_buff = ["OPEN_R","CLOSE_R","PHOTO_R"]
        data_flag = data_buff[randint(0,len(data_buff)-1)]
        # @ telmo - the following code you do apply
        send(service,client_socket,msg_ID,data_flag)
        msg_ID += 1
        # THE REST OF UR CODE #

def main():
    mobile_thread = threading.Thread(target=client,args=(network.MOBILE_CLIENT,))
    mobile_thread.start()
    urmain_mobile_thread = threading.Thread(target=yourMainLogic,args=(network.MOBILE_CLIENT,))
    urmain_mobile_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()