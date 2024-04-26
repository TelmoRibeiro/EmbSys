from utilities.message import message,message_unpack
from utilities.codec   import encode,decode
from utilities.log     import log
from utilities.network import CC_IPV4,MB_PORT,MC_PORT,MTC_PORT
from random            import randint
from time              import sleep
import socket
import threading

# @ telmo - no log polution?

def service_port(service):
    match service:
        case "MOBILE-SIM":
            return MB_PORT
        case "MULTIM-SIM":
            return MC_PORT
        case "MOUSET-SIM":
            return MTC_PORT
        case _: raise RuntimeError(f"service={service} not supported!")

def resume_connection(service,client_socket):
    data_recv = client_socket.recv(1024)
    data_decd = decode(data_recv)
    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
    log(f"{service}",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")
    if msg_ID != 0 or msg_content != "SYNC":
        raise RuntimeError(f"SYNC failed!")
    data_send = message(0,"SYNC_ACK")
    data_encd = encode(data_send)
    log(f"{service}",f"sending {data_send}...")
    client_socket.sendall(data_encd)

def send(service,client_socket,msg_ID,data_flag):
    # @ telmo - you do not want it to overwrite your data_flag
    # @ telmo - this is only for simulation purpose
    data_flag = ["OPEN_R","CLOSE_R","PHOTO_R","OPEN_E","CLOSE_E","PHOTO_E","SENSOR_E"]
    data_cont = data_flag[randint(0,len(data_flag)-1)]
    # @ telmo - you start from here!
    data_send = message(msg_ID,data_cont)
    data_encd = encode(data_send)
    log(f"{service}",f"sending {data_send}...")
    client_socket.sendall(data_encd)

def recv(service,msg_ID,msg_timestamp,msg_content):
    # @ telmo - function dealing with what you receive
    # @ telmo - for simulation purpose I will just log it
    # @ telmo - you may pattern match the content through the cases you are expecting
    log(f"{service}",f"received: {msg_ID} | {msg_timestamp} | {msg_content}")

def client(service):
    SERVICE_PORT  = service_port(service)
    try:
        # TCP CONNECTION #
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((CC_IPV4,SERVICE_PORT))
            log(f"{service}",f"connection established with {CC_IPV4}")  
            try:
                resume_connection(service,client_socket)
                msg_ID = 1
                while True:
                    # @ telmo - you do not want it to wait 5 seconds
                    # @ telmo - this is only for simulation purpouse
                    sleep(5)
                    # @ telmo - instead of having send in the while True
                    # @ telmo - you pass the parameters used in send
                    # @ telmo - and you call it every time you need it
                    send(service,client_socket,msg_ID,None)
                    # @ telmo - you do want the following receiving loop body
                    # @ telmo - always running on thread
                    # AVERAGE LOOP BODY #
                    data_recv = client_socket.recv(1024)
                    if not data_recv:
                        break
                    data_decd = decode(data_recv)
                    msg_ID,msg_timestamp,msg_content = message_unpack(data_decd)
                    recv(service,msg_ID,msg_timestamp,msg_content)
                    msg_ID += 1
            except Exception as e:
                log(f"{service}",f"error: {e}")
        except ConnectionRefusedError:
            log(f"{service}",f"connection with {CC_IPV4} refused")
        finally:
            client_socket.close()
    except KeyboardInterrupt:
        log(f"{service}",f"shutting down...")

def main():
    # @ telmo - comment the threads you are not implementing!
    mobile_thread = threading.Thread(target=client,args=("MOBILE-SIM",))
    multim_thread = threading.Thread(target=client,args=("MULTIM-SIM",))
    mouset_thread = threading.Thread(target=client,args=("MOUSET-SIM",))
    mobile_thread.start()
    multim_thread.start()
    mouset_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()