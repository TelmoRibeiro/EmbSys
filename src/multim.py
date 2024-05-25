import utilities.network   as network
from utilities.message import encode_packet,decode_packet,message_unpack # may remove this later
from utilities.log     import log_cnsl
import socket
import threading

# from picamera2 import Picamera2 # photos on arduino
# import serial                   # pyserial
import os                       # ???
import struct                   # header fix
from PIL import Image

PHOTO_DIRECTORY = "./pics/" # TEST WITHOUT ME
PHOTO_BUFF_SIZE =  5        # max #pics in buff

# EVENTS # 
SERVICE_ONLINE = threading.Event() # SERVICE ONLINE?
ARDUINO_EVENT  = threading.Event() # CLIENT -> ARD-CLIENT COMMS

def play(service,client_socket):
    try:
        while True:
            _,_,msg_flag = decode_packet(client_socket.recv(1024))    
            if msg_flag != "SYNC" and msg_flag != "NSYNC":
                log_cnsl(service,f"SYNC/NSYNC expected yet {msg_flag} received")
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
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        client_socket.close()

def send(service,client_socket,msg_ID,msg_flag):
    try:
        if not SERVICE_ONLINE.is_set():
            log_cnsl(service,f"sending {msg_flag}... service OFFLINE")
            client_socket.close()
            return
        _,data_encd = encode_packet(msg_ID,msg_flag)
        log_cnsl(service,f"sending {msg_flag}...")
        client_socket.sendall(data_encd)
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        client_socket.close()

def recv(service,msg_ID,msg_flag):
    global ARDUINO_GLOBAL
    match msg_flag:
        case "SHUTDOWN":
            log_cnsl(service,f"received {msg_flag}")
            SERVICE_ONLINE.clear()
        case "OPEN_R":
            log_cnsl(service,f"received {msg_flag}")
            _,ARDUINO_GLOBAL = encode_packet(msg_ID,msg_flag)
            ARDUINO_EVENT.set()
        case "CLOSE_R":
            log_cnsl(service,f"received {msg_flag}")
            _,ARDUINO_GLOBAL = encode_packet(msg_ID,msg_flag)
            ARDUINO_EVENT.set()
        case "PHOTO_R":
            log_cnsl(service,f"received {msg_flag}")
            # TO DO!
        case _: 
            log_cnsl(service,f"flag={msg_flag} not supported")
            SERVICE_ONLINE.clear()

def client(service):
    try:
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        SERVICE_IPV4  = network.SERVER_IPV4
        SERVICE_PORT  = network.service_port(service)
        try:
            client_socket.connect((SERVICE_IPV4,SERVICE_PORT))
            log_cnsl(service,f"connection established with {SERVICE_IPV4}")
            global SERVICE_SOCKET
            SERVICE_SOCKET = client_socket
            play(service,client_socket)
            SERVICE_ONLINE.set()
            try:
                while True:
                    if not SERVICE_ONLINE.is_set():
                        client_socket.close()
                        break
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        log_cnsl(service,f"received None")
                        SERVICE_ONLINE.clear()
                        client_socket.close()
                        break
                    msg_ID,_,msg_flag = decode_packet(data_recv)
                    recv(service,msg_ID,msg_flag)
            except Exception as e:
                log_cnsl(service,f"detected DOWNTIME | {e}")
                SERVICE_ONLINE.clear()
                client_socket.close()
        except ConnectionRefusedError:
            log_cnsl(service,f"connection with {SERVICE_IPV4} refused")
            SERVICE_ONLINE.clear()
            client_socket.close()
    except KeyboardInterrupt:
        log_cnsl(service,"shutting down...")
        SERVICE_ONLINE.clear()

def arduino_client(service):
    try:
        serial_socket = serial.Serial('/dev/ttyACM0',9600)
        serial_socket.reset_input_buffer()
        while not SERVICE_ONLINE.is_set():
            continue
        while True:
            if not SERVICE_ONLINE.is_set():
                serial_socket.close()
                break
            if serial_socket.in_waiting:
                msg_ID,msg_timestamp,msg_flag = decode_packet(serial_socket.readline())
                log_cnsl(service,f"received {msg_flag} from SERIAL")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,))
                message_control_thread.start()
            if ARDUINO_EVENT.is_set():
                ARDUINO_EVENT.clear() 
                global ARDUINO_GLOBAL
                msg_ID,msg_timestamp,msg_flag = decode_packet(ARDUINO_GLOBAL)
                log_cnsl(service,f"received {msg_flag} from WIFI")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,))
                message_control_thread.start()        
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        serial_socket.close()

def message_control(service,serial_socket,msg_ID,msg_timestamp,msg_flag):
    global ARDUINO_GLOBAL
    match msg_flag:
        case "SENSOR_E":
            send(service,SERVICE_SOCKET,msg_ID,msg_flag)
        case "OPEN_E":
            send(service,SERVICE_SOCKET,msg_ID,msg_flag)
        case "CLOSE_E":  
            send(service,SERVICE_SOCKET,msg_ID,msg_flag)
        case "OPEN_R":
            _,data_encd = encode_packet(msg_ID,msg_flag,msg_timestamp)
            serial_socket.write(data_encd)
            ARDUINO_GLOBAL = None
            ARDUINO_EVENT.clear()
        case "CLOSE_R":
            _,data_encd = encode_packet(msg_ID,msg_flag,msg_timestamp)
            serial_socket.write(data_encd)
            ARDUINO_GLOBAL = None
            ARDUINO_EVENT.clear()
        case _:
            log_cnsl(service,f"service={service} not supported")
            SERVICE_ONLINE.clear()
            serial_socket.close()
            SERVICE_SOCKET.close() # maybe not needed

def yourMainLogic(service):
    while not SERVICE_ONLINE.is_set():
        continue
    client_socket = SERVICE_SOCKET
    msg_ID = 1
    while True:
        if not SERVICE_ONLINE.is_set():
            return
        # @ telmo - for simulation purpose I will sleep 3 seconds and then call a random flag
        from time import sleep
        sleep(3)
        from random import randint
        data_buff = ["OPEN_E","CLOSE_E","PHOTO_E","SENSOR_E"]
        data_flag = data_buff[randint(0,len(data_buff)-1)]
        # @ telmo - the following code you do apply
        send(service,client_socket,msg_ID,data_flag) 
        msg_ID += 1
        # THE REST OF UR CODE #            

def main():
    multim_thread = threading.Thread(target=client,args=(network.MULTIM_CLIENT,))
    #mouset_thread = threading.Thread(target=arduino_client,args=("ARDUINO-CLNT",))
    multim_thread.start()
    urmain_thread = threading.Thread(target=yourMainLogic,args=("URMAIN",))
    urmain_thread.start()
    #mouset_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()