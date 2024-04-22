from utilities.message import message as message
from utilities.log     import log     as log
from utilities.codec   import encode,decode
from utilities.network import CC_IPV4,CC_PORT
import socket
import threading
from kivy.lang       import Builder
# from kivy.uix.widget import Widget
from kivymd.app      import MDApp

def client():
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client_socket.connect((CC_IPV4,CC_PORT))
            log("Mobile-BE",f"connection established with {CC_IPV4}")
            msg_ID = 1
            try:
                while True:
                    data_send = message(msg_ID,f"current msg_ID={msg_ID}")
                    data_encd = encode(data_send)
                    log("Mobile-BE",f"sending {data_send}...")
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
                    log("Mobile-BE",f"received ID={msg_ID} | content={msg_content} | timestamp={msg_timestamp}")
                    msg_ID += 1
            except Exception as e:
                log("Mobile-BE",f"error: {e}")
        except ConnectionRefusedError:
            log("Mobile-BE",f"connection with {CC_IPV4} refused")
        finally:
            client_socket.close()
    except KeyboardInterrupt:
        log("Mobile-BE",f"shutting down...")

Builder.load_file("gui.kv")

class MyWidget(BoxLayout):
    def btn_press(self):
        print("Button Pressed!")

class MobileApp(MDApp):
    def build(self):
        return MyWidget()

def screen():        
    MobileApp().run()

def main():
    log("Mobile",f"booting...")
    log("Mobile",f"creating threads...")
    # client_thread = threading.Thread(target=client)
    screen_thread = threading.Thread(target=screen)
    log("Mobile",f"waking threads...")
    # client_thread.start()
    screen_thread.start()
    return

if __name__ == "__main__": main()