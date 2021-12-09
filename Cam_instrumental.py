import numpy as np
import cv2
from instrumental import instrument, list_instruments
import keyboard
import functions_osc_python3 as osc
# from instrumental.log import log_to_screen
# log_to_screen()
import paths

# create the camera object (using the serial to ID it, use list_instruments() to get all of them)
cam = instrument(paths.cam_miniscope_serial)

# define the framerate
framerate = 25
# set the flash mode on the camera (to get triggers out)
cam.set_flash_mode(1, 'freerun_high')
# set the flash parameters
cam.set_flash_params(delay=1, duration=25000)

cam.pixelclock = '35MHz'
print(f'Current pixelclock: {cam.pixelclock}')

# # set exposure
# cam._set_exposure('38ms')

cam.set_framerate(framerate)
print(f'Current framerate: {cam.framerate}')

# print(f'Current exposure: {cam._get_exposure()}')
# # get the effective framerate and use on the video
# effective_exposure = cam._get_exposure().magnitude/1000
# effective_framerate = round(1/effective_exposure, 2)
#
# print(f'Current framerate: {effective_framerate}')

# configure the video codec for opencv
fourcc = cv2.VideoWriter_fourcc(*'XVID')
# initialize the video writer
out = cv2.VideoWriter('output.avi', fourcc, framerate, (1280, 1024))

# start the live capture
cam.start_live_video()
# for all the frames (replace with a while block)
# for frame_idx in np.arange(number_frames):
while True:
    # wait for the next available frame
    cam.wait_for_frame()
    # get the latest frame in the buffer
    frame = cam.latest_frame()
    # turn it to color so opencv can save it (issues with monochrome)
    frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    # write the frame to file
    out.write(frame)

    if keyboard.is_pressed('Escape'):
        break
# close the file
out.release()
# stop the acquisition
cam.stop_live_video()
# close the camera
cam.close()
