# import numpy as np
import time

import cv2
from instrumental import instrument, list_instruments
import keyboard
# from instrumental.log import log_to_screen
# log_to_screen()
# from pythonosc.osc_server import AsyncIOOSCUDPServer
# from pythonosc.dispatcher import Dispatcher
# import functions_osc_python3 as osc
from functions_osc4py3 import OSCManager
# import asyncio
import paths
import sys


# parse the external arguments
cam_serial = sys.argv[1]
out_path = sys.argv[2]
# initialize the control variable
controller = 3
# initialize the frame counter
frame_counter = 0

# set up the OSC communication
osc = OSCManager()

osc.create_server(paths.cam_ip, paths.cam_port, 'server_cam')
osc.create_client(paths.recorder_ip, paths.recorder_port, 'client_recorder')

# create the camera object (using the serial to ID it, use list_instruments() to get all of them)
cam = instrument(cam_serial)

# define the framerate
framerate = 25

# configure the video codec for opencv
fourcc = cv2.VideoWriter_fourcc(*'XVID')
# initialize the video writer
out = cv2.VideoWriter(out_path, fourcc, framerate, (1280, 1024))
# cv2.namedWindow('frame', cv2.WINDOW_AUTOSIZE)
# set the flash mode on the camera (to get triggers out)
cam.set_flash_mode(1, 'freerun_high')
# set the flash parameters
cam.set_flash_params(delay=1, duration=10000)
# set the pixel clock
cam.pixelclock = '35MHz'
print(f'Current pixelclock: {cam.pixelclock}')
# set the framerate in the camera
cam.set_framerate(framerate)
print(f'Current framerate: {cam.framerate}')
# start the live capture
cam.start_live_video()

# message the recorder that acquisition is ready
osc.send_release('client_recorder', 'cam')

# for all the frames (replace with a while block)
while True:
    # check status of the flag
    if osc.simple_message == 1:
        # wait for the next available frame
        cam.wait_for_frame()
        # get the latest frame in the buffer
        frame = cam.latest_frame()
        # display the image from the camera
        cv2.imshow('frame', frame)
        # wait a ms (required for imshow, doesn't seem to affect framerate)
        cv2.waitKey(1)
        # turn it to color so opencv can save it (issues with monochrome)
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
        # write the frame to file
        out.write(frame)
        # update the frame counter
        frame_counter += 1
    elif osc.simple_message == 2:
        cv2.destroyAllWindows()
        break
    else:
        time.sleep(0.01)

# print the number of frames recorded
print(f'Recorded frames: {frame_counter}')

# stop the osc
osc.stop()

# close the file
out.release()
# stop the acquisition
cam.stop_live_video()
# close the camera
cam.close()


