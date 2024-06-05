import utilities.directory as directory
from utilities.log         import log

from picamera2 import Picamera2 # type: ignore # photo handler (linux)
from time      import sleep

import threading

def photos_control(service):
    # photo reshoot main functionality
    try:
        cam = Picamera2()
        cam.configure(cam.create_still_configuration(main={"format": "XRGB8888","size":(720,480)}))
        cam.start()
        while True:
            photo_path = directory.PHOTO_DIR + "send.png"
            cam.capture_file(photo_path) # default delay = 1 sec
            sleep(1)                     # maybe not needed
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")

def main():
    while True:
        photos_thread = threading.Thread(target=photos_control,args=("PHOTOS-CNTRL",))
        photos_thread.start()
        # RUNNING THREADS #
        photos_thread.join()

if __name__ == "__main__": main()