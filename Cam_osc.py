import numpy as np
import cv2
from instrumental import instrument, list_instruments
import keyboard
# from instrumental.log import log_to_screen
# log_to_screen()
from pythonosc.osc_server import AsyncIOOSCUDPServer
from pythonosc.dispatcher import Dispatcher
import functions_osc_python3 as osc
import asyncio
import paths


def control_loop(address, *args):
    """Control the server for the camera interpreting the messages from the recorder"""
    global controller
    if args[0] == 0:
        controller = 0
    elif args[0] == 1:
        controller = 1
    else:
        controller = None
    return controller


# initialize the control variable
controller = 3
# initialize the frame counter
frame_counter = 0
# create and set up the dispatcher
dispatcher = Dispatcher()
dispatcher.map('/cam_loop', control_loop)

# create the camera object (using the serial to ID it, use list_instruments() to get all of them)
cam = instrument('4103437084')

# define the framerate
framerate = 30

# configure the video codec for opencv
fourcc = cv2.VideoWriter_fourcc(*'XVID')
# initialize the video writer
out = cv2.VideoWriter('output.avi', fourcc, framerate, (1280, 1024))

# set the flash mode on the camera (to get triggers out)
cam.set_flash_mode(1, 'freerun_high')
# set the flash parameters
cam.set_flash_params(delay=1, duration=10000)
# set the pixel clock
cam.pixelclock = '86MHz'
print(f'Current pixelclock: {cam.pixelclock}')
# set the framerate in the camera
cam.set_framerate(framerate)
print(f'Current framerate: {cam.framerate}')
# start the live capture
cam.start_live_video()


async def loop():
    """Loop to capture images"""
    global controller, frame_counter
    # for all the frames (replace with a while block)
    while True:
        # check status of the flag
        if controller == 1:
            # wait for the next available frame
            cam.wait_for_frame()
            # get the latest frame in the buffer
            frame = cam.latest_frame()
            # turn it to color so opencv can save it (issues with monochrome)
            frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
            # write the frame to file
            out.write(frame)
            # update the frame counter
            frame_counter += 1
        elif controller == 0:
            break
        # poll the server
        await asyncio.sleep(0)
        # TODO: remove once the system works
        if keyboard.is_pressed('Enter'):
            break


async def init_main():
    """Main server loop"""
    # create and configure the endpoint
    server = AsyncIOOSCUDPServer((paths.cam_ip, paths.cam_port), dispatcher, asyncio.get_event_loop())
    # Create datagram endpoint and start serving
    transport, protocol = await server.create_serve_endpoint()
    # message the recorder to start recording
    osc.create_send_close(paths.recorder_ip, paths.recorder_port, '/close', 'close_server')
    # Enter main loop of program
    await loop()

    # print the number of frames recorded
    print(f'Recorded frames: {frame_counter}')
    # Clean up serve endpoint
    transport.close()

    # close the file
    out.release()
    # stop the acquisition
    cam.stop_live_video()
    # close the camera
    cam.close()

# run the server and loop
asyncio.run(init_main())

