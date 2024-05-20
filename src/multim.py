import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl
from time              import sleep
from random            import randint
import socket
import threading
import serial

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
PLAY_EVENT = threading.Event() # used to notify communication can begin

def play(service,client_socket):
    try:
        _,_,msg_content = decode_packet(client_socket.recv(1024))
        log_cnsl(service,"received SYNC!")    
        if msg_content != "SYNC":
            log_cnsl(service,f"SYNC expected yet {msg_content} received!")
            client_socket.close()
        ##########
        _,data_encd = encode_packet(0,"SYNC_ACK")
        log_cnsl(service,f"sending SYNC_ACK...")
        client_socket.sendall(data_encd)
    except Exception as e:
        log_cnsl(service,f"caught: {e}")
        client_socket.close()

# call this function whenever you want to send data as long as play event is set #
def send(service,client_socket,msg_ID,msg_content):
    try:
        _,data_encd = encode_packet(msg_ID,msg_content)
        log_cnsl(service,f"sending {msg_content}...")
        client_socket.sendall(data_encd)
    except Exception as e:
        log_cnsl(service,f"catched: {e}")
        client_socket.close()

# modify this function to pattern match and treat what you will receive #
def recv(service,msg_ID,msg_timestamp,msg_content):
    # @ telmo - for simulation purpose I will just log it
    match msg_content:
        case _: log_cnsl(service,f"received {msg_content}!")

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
            PLAY_EVENT.set()
            try:
                while True:
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    msg_ID,msg_timestamp,msg_content = decode_packet(data_recv)
                    recv(service,msg_ID,msg_timestamp,msg_content)
            except Exception as e:
                log_cnsl(service,f"caught: {e}")
            finally:
                client_socket.close()
        except ConnectionRefusedError:
            log_cnsl(service,f"connection with {SERVICE_IPV4} refused")
        finally:
            client_socket.close()
    except KeyboardInterrupt:
        log_cnsl(service,"shutting down...")

def yourMainLogic(service):
    while not PLAY_EVENT.is_set():
        continue
    client_socket = SERVICE_SOCKET
    msg_ID = 1
    while True:
        # @ telmo - for simulation purpose I will sleep 3 seconds and then call a random flag
        sleep(3)
        data_buff = ["OPEN_E","CLOSE_E","SENSOR_E","PHOTO_E"]
        data_flag = data_buff[randint(0,len(data_buff)-1)]
        # @ telmo - the following code you do apply
        send(service,client_socket,msg_ID,data_flag) 
        msg_ID += 1
        # THE REST OF UR CODE #

def main():
    multim_thread = threading.Thread(target=client,args=(network.MULTIM_CLIENT,))
    multim_thread.start()
    urmain_multim_thread = threading.Thread(target=yourMainLogic,args=(network.MULTIM_CLIENT,))
    urmain_multim_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()