import utilities.network   as network
import utilities.directory as directory
from utilities.message     import encode_packet,decode_packet
from utilities.log         import log

from threading import Thread,Event
from struct    import pack,unpack

import socket # enables communication with peers
import serial # enables communication with arduino

# NETWORK:
SERVICE_IPV4 = network.SERVER_IPV4

# STATUS:
DOOR_STATUS = "OPEN_R"

# EVENTS #
SERVICE_ONLINE = Event() # service status
ARDUINO_EVENT  = Event() # communication client -> arduino_client

def client(service):
    # main functionality
    try:
        client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        SERVICE_PORT  = network.service_port(service)
        try:
            client_socket.connect((SERVICE_IPV4,SERVICE_PORT))
            global SERVICE_SOCKET
            SERVICE_SOCKET = client_socket
            log(service,f"connection established with {SERVICE_IPV4}")
            play(service) # @ telmo - maybe check this
            SERVICE_ONLINE.set()
            while True:
                if not SERVICE_ONLINE.is_set():
                    SERVICE_SOCKET.close()
                    return
                header = recv_all(service,4)
                if not header:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                length = unpack("!I",header)[0]
                data_recv = recv_all(service,length)
                # log(service,f"received (RAW) {data_recv}")
                if not data_recv:
                    log(service,f"detected DOWNTIME (recv) | received nothing")
                    SERVICE_ONLINE.clear()
                    SERVICE_SOCKET.close()
                    return
                msg_flag,msg_content,_ = decode_packet(data_recv)
                log(service,f"received {msg_flag}")
                recv(service,msg_flag,msg_content)
        except ConnectionRefusedError:
            log(service,f"connection with {SERVICE_IPV4} refused")
            SERVICE_ONLINE.clear()
    except KeyboardInterrupt:
        log(service,"shutting down...")
        SERVICE_ONLINE.clear()

def recv(service,msg_flag,msg_content):
    # patttern matches the received fields into functions
    try:
        global ARDUINO_GLOBAL
        match msg_flag:
            case "SHUTDOWN":
                SERVICE_ONLINE.clear()
                SERVICE_SOCKET.close()
            case "OPEN_R":
                _,ARDUINO_GLOBAL = encode_packet(msg_flag,msg_content)
                ARDUINO_EVENT.set()
            case "CLOSE_R":
                _,ARDUINO_GLOBAL = encode_packet(msg_flag,msg_content)
                ARDUINO_EVENT.set()
            case "PHOTO_R":
                photo_path = directory.PHOTO_DIR + "send.png"
                with open(photo_path,"rb") as photo_file:
                    photo_data = photo_file.read()
                send(service,"PHOTO_E",photo_data.hex())
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
                # log(service,f"received (RAW) {data_recv}")
                msg_flag,msg_content,_ = decode_packet(data_recv)
                log(service,f"received {msg_flag} from SERIAL")
                message_control_thread = Thread(target=message_control,args=(service,serial_socket,msg_flag,msg_content,))
                message_control_thread.start()
            if ARDUINO_EVENT.is_set():
                data_recv = ARDUINO_GLOBAL
                # log(service,f"received (RAW) {data_recv}")
                msg_flag,msg_content,_ = decode_packet(data_recv)
                ARDUINO_EVENT.clear()
                log(service,f"received {msg_flag} from WIFI")
                message_control_thread = Thread(target=message_control,args=(service,serial_socket,msg_flag,msg_content,))
                message_control_thread.start()
    except Exception as e:
        log(service,f"detected DOWNTIME | {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def message_control(service,serial_socket,msg_flag,msg_content):
    # controls the expected behaviour according to the received message
    try:
        match msg_flag:
            case EVENT if EVENT in ["OPEN_E","CLOSE_E","SENSOR_E"]:
                if EVENT != "SENSOR_E":
                    global DOOR_STATUS
                    DOOR_STATUS = EVENT
                send(service,msg_flag,msg_content)
            case REQUEST if REQUEST in ["OPEN_R","CLOSE_R"]:
                _,data_encd = encode_packet(msg_flag,msg_content)
                serial_socket.write(data_encd)
            case _:
                serial_socket.close()
                raise Exception(f"flag={msg_flag} not supported")
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")
        SERVICE_ONLINE.clear()
        SERVICE_SOCKET.close()

def play(service):
    # handshake that unjams this endpoint
    # used to sync all endpoints
    try:
        global DOOR_STATUS
        while True:
            header = recv_all(service,4)
            if not header:
                raise Exception("received nothing [header]")
            length = unpack("!I",header)[0]
            data_recv = recv_all(service,length)
            if not data_recv:
                raise Exception("received nothing [body]")
            msg_flag,msg_content,_ = decode_packet(data_recv)
            match msg_flag:
                case SYNC if SYNC in ["SYNC"]:
                    log(service,f"received {msg_flag} - {msg_content}")
                    DOOR_STATUS = msg_content
                    send(service,"SYNC_ACK")
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

def send(service,msg_flag,msg_content=None):
    # sends a message through the provided socket
    # it encodes said message before sending
    try:
        _,data_encd = encode_packet(msg_flag,msg_content)
        log(service,f"sending {msg_flag}...")
        length = pack("!I",len(data_encd))
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
    while True:
        multim_thread = Thread(target=client,args=(network.MULTIM_CLIENT,))
        mouset_thread = Thread(target=arduino_client,args=("ARDUINO-CLNT",))
        SERVICE_ONLINE.clear()
        ARDUINO_EVENT.clear()
        multim_thread.start()
        mouset_thread.start()
        # RUNNING THREADS #
        multim_thread.join()
        mouset_thread.join()

if __name__ == "__main__": main()