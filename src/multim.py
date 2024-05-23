import utilities.network   as network
from utilities.message import encode_packet,decode_packet
from utilities.log     import log_cnsl
from time              import sleep,time
import socket
import threading

#from picamera2 import Picamera2 # photos on RASPI
import serial                   # pyserial
import struct                   # header fix
import os
from PIL import Image

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

# PHOTO_DIRECTORY = "./pics/" # save pics here! / TEST WITHOUT ME
# PHOTO_BUFF_SIZE =  5        # max #pics in buff

# EVENTS # 
SERVICE_ONLINE = threading.Event() # SERVICE ONLINE?
ARDUINO_EVENT  = threading.Event() # MULTIM INTERCEPTED COMMS TO ARDUINO

'''
class PhotoThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.photo_buffer = []  # Buffer to store photos
        self.buffer_lock = threading.Lock()
        self.stop_event  = threading.Event()
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size   = (1280,720)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.preview_configuration.align()
        self.picam2.configure("preview")
        self.picam2.start()
    def run(self):
        while not self.stop_event.is_set():
            # Take a photo
            photo_path = self.take_photo()
            # Add the photo to the buffer
            self.add_to_buffer(photo_path)
            # Sleep for a while before taking the next photo
            sleep(1)

    def take_photo(self):
        # Capture an image with picamera2
        im = self.picam2.capture_array()
        # Save the photo to a file
        photo_path = os.path.join(PHOTO_DIRECTORY,f"photo_{int(time())}.png")
        #cv2.imwrite(photo_path, im)
        image = Image.fromarray(im)
        image.save(photo_path)
        return photo_path

    def add_to_buffer(self, photo_path):
        with self.buffer_lock:
            # Add the photo to the buffer
            self.photo_buffer.append(photo_path)
            #log_cnsl("MC-SERVER", f"Added new photo: {photo_path}")

        if len(self.photo_buffer) > PHOTO_BUFF_SIZE:
            oldest_photo = self.photo_buffer.pop(0)
            if os.path.exists(oldest_photo):
                try:
                    os.remove(oldest_photo)
                except Exception as e:
                    log_cnsl("PIC",f"could not remove the oldest pic...")

    def get_latest_photo(self):
        if self.photo_buffer:
            return self.photo_buffer[-1]
        else:
            return None

    def stop(self):
        # Set the stop event to signal the thread to stop
        self.stop_event.set()
        # Stop the camera
        self.picam2.stop()
        self.picam2.close()
'''

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
        _,data_encd = encode_packet(0,"SYNC_ACK",None)
        log_cnsl(service,f"sending SYNC_ACK...")
        client_socket.sendall(data_encd)
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME")
        SERVICE_ONLINE.clear()
        client_socket.close()

# call this function whenever you want to send data as long as play event is set #
def send(service,client_socket,msg_ID,msg_flag,msg_content):
    try:
        if not SERVICE_ONLINE.is_set():
            log_cnsl(service,f"NO CONNECTION!")
            client_socket.close()
            return
        _,data_encd = encode_packet(msg_ID,msg_flag,msg_content)
        log_cnsl(service,f"sending {msg_flag}...")
        client_socket.sendall(data_encd)
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME")
        SERVICE_ONLINE.clear()
        client_socket.close()

def recv(service,msg_ID,msg_timestamp,msg_flag):
    # @ telmo - for simulation purpose I will just log it
    global PROTOA_GLOBAL
    match msg_flag:
        case "SHUTDOWN":
            log_cnsl(service,f"received SHUTDOWN")
            SERVICE_ONLINE.clear()
        case "OPEN_R":
            log_cnsl(service,f"received OPEN_R")
            data_send,PROTOA_GLOBAL = encode_packet(msg_ID,msg_flag,None)
            log_cnsl(service,f"forwarding to ARD-CLNT: {data_send}")
            ARDUINO_EVENT.set()
        case "CLOSE_R":
            log_cnsl(service,f"received CLOSE_R")
            data_send,PROTOA_GLOBAL = encode_packet(msg_ID,msg_flag,None)
            log_cnsl(service,f"forwarding to ARD-CLNT: {data_send}")
            ARDUINO_EVENT.set()
        case "PHOTO_R":
            log_cnsl(service,f"received PHOTO_R")
            '''
            pic_path = PHOTO_DIRECTORY + "\text.png"
            pic_file = open(pic_path,"rb")
            pic_data = pic_file.read()
            '''
        case _: 
            log_cnsl(service,f"service={msg_flag} not supported!")
            SERVICE_ONLINE.clear()

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
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        SERVICE_ONLINE.clear()
                        break
                    msg_ID,msg_timestamp,msg_flag = decode_packet(data_recv)
                    recv(service,msg_ID,msg_timestamp,msg_flag)
            except Exception as e:
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

def arduino_client(service):
    try:
        serial_socket = serial.Serial('/dev/ttyACM0',9600)
        serial_socket.reset_input_buffer()
        while not SERVICE_ONLINE.is_set():
            continue
        while True:
            if not SERVICE_ONLINE.is_set():
                break # CHECK THIS
            # not 100%
            if serial_socket.in_waiting:
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(serial_socket.readline())
                print(message) # remove this
                log_cnsl(service,f"received {msg_flag} from SERIAL")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content,))
                message_control_thread.start()
            if ARDUINO_EVENT.is_set():
                ARDUINO_EVENT.clear() 
                global PROTOA_GLOBAL
                message = PROTOA_GLOBAL
                msg_ID,msg_timestamp,msg_flag,msg_content = decode_packet(message)
                log_cnsl(service,f"received {msg_flag} from WIFI")
                message_control_thread = threading.Thread(target=message_control,args=(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content,))
                message_control_thread.start()        
    except Exception as e:
        log_cnsl(service,f"detected DOWNTIME {e}")
        SERVICE_ONLINE.clear()
        serial_socket.close()

def message_control(service,serial_socket,msg_ID,msg_timestamp,msg_flag,msg_content):
    global PROTOA_GLOBAL
    match msg_flag:
        case "SENSOR_E":
            client_socket = SERVICE_SOCKET
            send(service,client_socket,msg_ID,msg_flag,msg_content)
        case "OPEN_E":
            client_socket = SERVICE_SOCKET
            send(service,client_socket,msg_ID,msg_flag,msg_content)
        case "CLOSE_E":
            client_socket = SERVICE_SOCKET  
            send(service,client_socket,msg_ID,msg_flag,msg_content)
        case "OPEN_R":
            _,message = encode_packet(msg_ID,msg_flag,msg_content,msg_timestamp)
            serial_socket.write(message)
            PROTOA_GLOBAL = None
            ARDUINO_EVENT.clear()
        case "CLOSE_R":
            _,message = encode_packet(msg_ID,msg_flag,msg_content,msg_timestamp)
            serial_socket.write(message)
            PROTOA_GLOBAL = None
            ARDUINO_EVENT.clear()
        case _:
            log_cnsl(service,f"service={service} not supported!")
            SERVICE_ONLINE.clear()
            serial_socket.close()
            client_socket = SERVICE_SOCKET  # maybe not needed
            client_socket.close()           # maybe not needed
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
        sleep(3)
        data_buff = ["SENSOR_E"]
        data_flag = data_buff[randint(0,len(data_buff)-1)]
        # @ telmo - the following code you do apply
        send(service,client_socket,msg_ID,data_flag) 
        msg_ID += 1
        # THE REST OF UR CODE #
'''

def main():
    if not os.path.exists(PHOTO_DIRECTORY):
        os.mkdir(PHOTO_DIRECTORY)
    # sleep(3) # try without me
    multim_thread = threading.Thread(target=client,args=(network.MULTIM_CLIENT,))
    mouset_thread = threading.Thread(target=arduino_client,args=(network.MULTIM_CLIENT+"-ARD",))
    multim_thread.start()
    mouset_thread.start()
    
    #urmain_multim_thread = threading.Thread(target=yourMainLogic,args=(network.MULTIM_CLIENT,))
    #urmain_multim_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()