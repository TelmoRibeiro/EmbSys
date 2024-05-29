import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl

# from picamera2 import Picamera2 # photos on arduino
import threading
import socket
import struct
import serial
import os

PHOTO_DIRECTORY = "./pics/"

# EVENTS # 
SERVICE_ONLINE = threading.Event() # SERVICE ONLINE?
ARDUINO_EVENT  = threading.Event() # CLIENT -> ARD-CLIENT COMMS

def play(service):
    while True:
        _,_,msg_flag,_ = decode_packet(SERVICE_SOCKET.recv(1024)) # not testing if none
        match msg_flag:
            case SYNC if SYNC in ["SYNC"]:
                log_cnsl(service,"received SYNC")
                _,data_encd = encode_packet(0,"SYNC_ACK")
                log_cnsl(service,"sending SYNC_ACK...")
                SERVICE_SOCKET.sendall(data_encd)
                return
            case NSYNC if NSYNC in ["NSYNC"]:
                log_cnsl(service,"received NSYNC")
                continue
            case _:
                log_cnsl(service,f"SYNC/NSYNC expected yet {msg_flag} received")
                SERVICE_ONLINE.clear()
                SERVICE_SOCKET.close()
                return

def send(service,msg_ID,msg_flag,msg_content=None):
    try:
        if not SERVICE_ONLINE.is_set():
            log_cnsl(service,f"sending {msg_flag}... service OFFLINE")
            SERVICE_SOCKET.close()
            return
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_content)
        log_cnsl(service,f"sending {msg_flag}...")
        length = struct.pack("!I",len(data_encd))
        SERVICE_SOCKET.sendall(length + data_encd)
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def recv_all(service,length):
    try:
        data_read = bytearray()
        while len(data_read) < length:
            chunk = SERVICE_SOCKET.recv(length - len(data_read))
            if not chunk:
                raise Exception("received nothing")
            data_read.extend(chunk)
        return bytes(data_read)
    except Exception as e:
        log_cnsl(service,f"DETECTED DOWNTIME | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def recv(service,msg_ID,msg_timestamp,msg_flag,msg_content):
    global ARDUINO_GLOBAL
    match msg_flag:
        case "SHUTDOWN":
            SERVICE_ONLINE.clear()
            SERVICE_SOCKET.close()
        case "OPEN_R":
            _,ARDUINO_GLOBAL = encode_packet(msg_ID,msg_flag,msg_content,msg_timestamp)
            ARDUINO_EVENT.set()
        case "CLOSE_R":
            _,ARDUINO_GLOBAL = encode_packet(msg_ID,msg_flag,msg_content,msg_timestamp)
            ARDUINO_EVENT.set()
        case "PHOTO_R":
            photo_path = PHOTO_DIRECTORY + "test.jpeg"
            with open(photo_path,"rb") as photo_file:
                photo_data = photo_file.read()
            send(service,msg_ID,"PHOTO_E",photo_data.hex())
        case _:
            log_cnsl(service,f"flag={msg_flag} not supported")
            SERVICE_ONLINE.clear()
            SERVICE_SOCKET.close()

def client(service):
    try:
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        SERVICE_IPV4  = network.SERVER_IPV4
        SERVICE_PORT  = network.service_port(service)
        try:
            client_socket.connect((SERVICE_IPV4,SERVICE_PORT))
            global SERVICE_SOCKET
            SERVICE_SOCKET = client_socket
            log_cnsl(service,f"connection established with {SERVICE_IPV4}")
            play(service)
            SERVICE_ONLINE.set()
            while True:
                if not SERVICE_ONLINE.is_set():
                    SERVICE_SOCKET.close()
                    return
                header = recv_all(service,4)
                if not header:
                    log_cnsl(service,f"received None")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                length = struct.unpack("!I",header)[0]
                data_recv = recv_all(service,length)
                if not data_recv:
                    log_cnsl(service,f"received None")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(data_recv)
                log_cnsl(service,f"received {msg_flag}")
                recv(service,msg_ID,msg_timestamp,msg_flag,msg_content)
        except ConnectionRefusedError:
            log_cnsl(service,f"connection with {SERVICE_IPV4} refused")
            SERVICE_ONLINE.clear()
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
                log_cnsl(service,"shutting down...")
                serial_socket.close()
                return
            if serial_socket.in_waiting:
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(serial_socket.readline())
                log_cnsl(service,f"received {msg_flag} from SERIAL")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content,))
                message_control_thread.start()
            if ARDUINO_EVENT.is_set():
                # global ARDUINO_GLOBAL
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(ARDUINO_GLOBAL)
                ARDUINO_EVENT.clear()
                log_cnsl(service,f"received {msg_flag} from WIFI")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content,))
                message_control_thread.start()        
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()
        serial_socket.close()

def message_control(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content):
    match msg_flag:
        case EVENT if EVENT in ["OPEN_E","CLOSE_E","SENSOR_E"]:
            send(service,msg_ID,msg_flag,msg_content)
        case REQUEST if REQUEST in ["OPEN_R","CLOSE_R"]:
            _,data_encd = encode_packet(msg_ID,msg_flag,msg_content,msg_timestamp)
            serial_socket.write(data_encd)
        case _:
            log_cnsl(service,f"flag={msg_flag} not supported")
            SERVICE_ONLINE.clear()
            SERVICE_SOCKET.close()
            serial_socket.close()
        
def main():
    multim_thread = threading.Thread(target=client,args=(network.MULTIM_CLIENT,))
    mouset_thread = threading.Thread(target=arduino_client,args=("ARDUINO-CLNT",))
    multim_thread.start()
    mouset_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()