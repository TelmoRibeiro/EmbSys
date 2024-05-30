import utilities.network   as network
import utilities.directory as directory
from utilities.message     import encode_packet,decode_packet
from utilities.log         import log

import threading
import socket
import struct
import serial  # enables communication with arduino 
from time      import sleep
from picamera2 import Picamera2 # type: ignore # photo handler (linux)

# NETWORK:
SERVICE_IPV4  = network.SERVER_IPV4

# EVENTS #
SERVICE_ONLINE = threading.Event() # service status
ARDUINO_EVENT  = threading.Event() # communication client -> arduino_client

def client(service):
    # main functionality
    try:
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        SERVICE_PORT  = network.service_port(service)
        try:
            client_socket.connect((SERVICE_IPV4,SERVICE_PORT))
            global SERVICE_SOCKET
            SERVICE_SOCKET = client_socket
            SERVICE_ONLINE.set()
            log(service,f"connection established with {SERVICE_IPV4}")
            play(service) # check bool
            while True:
                if not SERVICE_ONLINE.is_set():
                    log(service,f"detected DOWNTIME - service OFFLINE")
                    SERVICE_SOCKET.close()
                    return
                header = recv_all(service,4)
                if not header:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                length = struct.unpack("!I",header)[0]
                data_recv = recv_all(service,length)
                log(service,f"received (RAW) {data_recv}")
                if not data_recv:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(data_recv)
                log(service,f"received {msg_flag}")
                recv(service,msg_ID,msg_timestamp,msg_flag,msg_content)
        except ConnectionRefusedError:
            log(service,f"connection with {SERVICE_IPV4} refused")
            SERVICE_ONLINE.clear()
    except KeyboardInterrupt:
        log(service,"shutting down...")
        SERVICE_ONLINE.clear()

def recv(service,msg_ID,msg_timestamp,msg_flag,msg_content):
    # patttern matches the received fields into functions
    try:
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
                photo_path = directory.PHOTO_DIR + "send.png"
                with open(photo_path,"rb") as photo_file:
                    photo_data = photo_file.read()
                send(service,msg_ID,"PHOTO_E",photo_data.hex())
            case _:
                raise Exception(f"flag={msg_flag} not supported")
    except Exception as e:
        log(service,f"detected DOWNTIME (recv) | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def arduino_client(service):
    # arduino communication main functionality
    try:
        serial_socket = serial.Serial('/dev/ttyACM0',9600)
        serial_socket.reset_input_buffer()
        while not SERVICE_ONLINE.is_set():
            continue
        while True:
            if not SERVICE_ONLINE.is_set():
                serial_socket.close()
                raise Exception("detected DOWNTIME | service OFFLINE")
            if serial_socket.in_waiting:
                data_recv = serial_socket.readline()
                log(service,f"received (RAW) {data_recv}")
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(data_recv)
                log(service,f"received {msg_flag} from SERIAL")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content,))
                message_control_thread.start()
            if ARDUINO_EVENT.is_set():
                data_recv = ARDUINO_GLOBAL
                log(service,f"received (RAW) {data_recv}")
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(data_recv)
                ARDUINO_EVENT.clear()
                log(service,f"received {msg_flag} from WIFI")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content,))
                message_control_thread.start()
    except Exception as e:
        log(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def message_control(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content):
    # controls the expected behaviour according to the received message
    try:
        match msg_flag:
            case EVENT if EVENT in ["OPEN_E","CLOSE_E","SENSOR_E"]:
                send(service,msg_ID,msg_flag,msg_content)
            case REQUEST if REQUEST in ["OPEN_R","CLOSE_R"]:
                _,data_encd = encode_packet(msg_ID,msg_flag,msg_content,msg_timestamp)
                serial_socket.write(data_encd)
            case _:
                serial_socket.close()
                raise Exception(f"flag={msg_flag} not supported")
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def photos_control(service):
    # photo reshoot main functionality
    try:
        cam = Picamera2()
        cam.configure(cam.create_still_configuration(main={"format": "XRGB8888","size":(720,480)}))
        cam.start()
        while True:
            if not SERVICE_ONLINE.is_set():
                raise Exception("detected DOWNTIME | service OFFLINE")
            photo_path = directory.PHOTO_DIR + "send.png"
            cam.capture_file(photo_path) # default delay = 1 sec
            sleep(1)                     # maybe not needed
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def play(service):
    # handshake that unjams this endpoint
    # used to sync all endpoints
    try:
        while True:
            header = recv_all(service,4)
            if not header:
                raise Exception("received nothing [header]")
            length = struct.unpack("!I",header)[0]
            data_recv = recv_all(service,length)
            if not data_recv:
                raise Exception("received nothing [body]")
            _,_,msg_flag,_ = decode_packet(data_recv)
            match msg_flag:
                case SYNC if SYNC in ["SYNC"]:
                    log(service,"received SYNC")
                    send(service,0,"SYNC_ACK")
                    return True
                case NSYNC if NSYNC in ["NSYNC"]:
                    log(service,"received NSYNC")
                    continue
                case _:
                    raise Exception(f"SYNC/NSYNC expected yet {msg_flag} received")
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()
        return False

def send(service,msg_ID,msg_flag,msg_content=None):
    # sends a message through the provided socket
    # it encodes said message before sending
    try:
        if not SERVICE_ONLINE.is_set():
            log(service,f"detected DOWNTIME (send) | service OFFLINE")
            SERVICE_SOCKET.close()
            return False
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_content)
        log(service,f"sending {msg_flag}...")
        length = struct.pack("!I",len(data_encd))
        SERVICE_SOCKET.sendall(length + data_encd)
        return True
    except Exception as e:
        log(service,f"detected DOWNTIME (send) | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()
        return False

def recv_all(service,length):
    # revieves messages from the provided socket
    # utilizes length in order to read just the necessary
    try:
        data_read = bytearray()
        while len(data_read) < length:
            chunk = SERVICE_SOCKET.recv(length - len(data_read))
            if not chunk:
                raise Exception("detected DOWNTIME (recv) | received nothing")
            data_read.extend(chunk)
        return bytes(data_read)
    except Exception as e:
        log(service,f"detected DOWNTIME (recv) | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()
        return None

def main():
    from sys import argv
    if len(argv) == 2:
        global SERVICE_IPV4
        SERVICE_IPV4 = argv[1]
    multim_thread = threading.Thread(target=client,args=(network.MULTIM_CLIENT,))
    mouset_thread = threading.Thread(target=arduino_client,args=("ARDUINO-CLNT",))
    photos_thread = threading.Thread(target=photos_control,args=("PHOTOS-CNTRL",))
    multim_thread.start()
    mouset_thread.start()
    photos_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()