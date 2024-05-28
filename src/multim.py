import utilities.network   as network
from utilities.message import encode_packet,decode_packet,message_unpack # may remove this later
from utilities.log     import log_cnsl

# from picamera2 import Picamera2 # photos on arduino
import threading
import socket
import struct
import serial
import os

PHOTO_DIRECTORY = "./pics/" # TEST WITHOUT ME
PHOTO_BUFF_SIZE =  5        # max #pics in buff

# EVENTS # 
SERVICE_ONLINE = threading.Event() # SERVICE ONLINE?
ARDUINO_EVENT  = threading.Event() # CLIENT -> ARD-CLIENT COMMS

def play(service,client_socket):
    try:
        while True:
            _,_,msg_flag,_,_ = decode_packet(client_socket.recv(1024))    
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

def send(service,client_socket,msg_ID,msg_flag,msg_length=0,msg_content=None):
    try:
        if not SERVICE_ONLINE.is_set():
            log_cnsl(service,f"sending {msg_flag}... service OFFLINE")
            client_socket.close()
            return
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_length,msg_content)
        log_cnsl(service,f"sending {msg_flag}...")
        packet_length = struct.pack("!I",len(data_encd)) # testing
        client_socket.sendall(packet_length + data_encd) # testing
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        client_socket.close()

def recv_all(client_socket,length):
    data_read = bytearray()
    while len(data_read) < length:
        chunk = client_socket.recv(length - len(data_read))
        if not chunk:
            raise Exception("received nothing")
        data_read.extend(chunk)
    return bytes(data_read)           

def recv(service,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content):
    global ARDUINO_GLOBAL
    match msg_flag:
        case "SHUTDOWN":
            log_cnsl(service,f"received {msg_flag}")
            SERVICE_ONLINE.clear()
            SERVICE_SOCKET.close()
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
            photo_path = PHOTO_DIRECTORY + "test.jpeg"
            with open(photo_path,"rb") as photo_file:
                photo_data = photo_file.read()
            send(service,SERVICE_SOCKET,msg_ID,"PHOTO_E",len(photo_data),photo_data.hex())
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
                    header = recv_all(client_socket,4)
                    data_length = struct.unpack("!I",header)[0]
                    data_recv = recv_all(client_socket,data_length)
                    if not data_recv:
                        log_cnsl(service,f"received None")
                        SERVICE_ONLINE.clear()
                        client_socket.close()
                        break
                    msg_ID,msg_timestamp,msg_flag,msg_length,msg_content = decode_packet(data_recv)
                    recv(service,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content)
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
                # log it
                serial_socket.close()
                break
            if serial_socket.in_waiting:
                msg_ID,msg_timestamp,msg_flag,msg_length,msg_content = decode_packet(serial_socket.readline())
                log_cnsl(service,f"received {msg_flag} from SERIAL")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content,))
                message_control_thread.start()
            if ARDUINO_EVENT.is_set():
                global ARDUINO_GLOBAL
                msg_ID,msg_timestamp,msg_flag,msg_length,msg_content = decode_packet(ARDUINO_GLOBAL)
                ARDUINO_EVENT.clear()
                log_cnsl(service,f"received {msg_flag} from WIFI")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content,))
                message_control_thread.start()        
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        serial_socket.close()

def message_control(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_length,msg_content):
    global ARDUINO_GLOBAL
    match msg_flag:
        case "SENSOR_E":
            send(service,SERVICE_SOCKET,msg_ID,msg_flag,msg_length,msg_content)
        case "OPEN_E":
            send(service,SERVICE_SOCKET,msg_ID,msg_flag,msg_length,msg_content)
        case "CLOSE_E":  
            send(service,SERVICE_SOCKET,msg_ID,msg_flag,msg_length,msg_content)
        case "OPEN_R":
            _,data_encd = encode_packet(msg_ID,msg_flag,msg_timestamp,msg_length,msg_content)
            serial_socket.write(data_encd)
            ARDUINO_GLOBAL = None
            ARDUINO_EVENT.clear()
        case "CLOSE_R":
            _,data_encd = encode_packet(msg_ID,msg_flag,msg_timestamp,msg_length,msg_content)
            serial_socket.write(data_encd)
            ARDUINO_GLOBAL = None
            ARDUINO_EVENT.clear()
        case _:
            log_cnsl(service,f"service={service} not supported")
            SERVICE_ONLINE.clear()
            serial_socket.close()
            SERVICE_SOCKET.close() # maybe not needed

'''
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
'''
        
def main():
    multim_thread = threading.Thread(target=client,args=(network.MULTIM_CLIENT,))
    mouset_thread = threading.Thread(target=arduino_client,args=("ARDUINO-CLNT",))
    multim_thread.start()
    mouset_thread.start()
    #urmain_thread = threading.Thread(target=yourMainLogic,args=("URMAIN",))
    #urmain_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()