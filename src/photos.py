import utilities.directory as directory
from utilities.log         import log

from picamera2 import Picamera2 # type: ignore # photo handler (linux)
from time      import sleep

import threading

def photos_control(service):
    # photo reshoot main functionality
    try:
        photo_path = directory.PHOTO_DIR + "send.png"
        cam = Picamera2()
        cam.configure(cam.create_still_configuration(main={"format":"XRGB8888","size":(720,480)}))
        cam.start()
        while True:
            cam.capture_file(photo_path)
            log(service,f"photo captured")
            sleep(1)
    except Exception as e:
        log(service,f"detected DOWNTIME | caught {e}")

def main():
    photos_thread = threading.Thread(target=photos_control,args=("PHOTOS-CNTRL",))
    photos_thread.start()
    # RUNNING THREADS #

if __name__ == "__main__": main()