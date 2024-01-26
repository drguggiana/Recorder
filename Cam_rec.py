import cv2
# import pylablib as pll
# pll.par["devices/dlls/uc480"] = "path/to/dlls"
from pylablib.devices import uc480
import matplotlib.pyplot as plt
import datetime
import numpy as np
# from instrumental import instrument, list_instruments
# from instrumental.log import log_to_screen
# log_to_screen()
# import instrumental.cam.uc480
# if __name__ == "__main__":
# print(uc480.list_cameras())
cam = uc480.UC480Camera()

# cam.set_exposure(10E-3)  # set 10ms exposure
# cam.set_roi(0, 128, 0, 128)  # set 128x128px ROI in the upper left corner
print(cam.get_full_info())
# set pixel rate (max found through cam.get_full_info
# cam.set_pixel_rate(86000000)
# cam.set_device_variable('trigger_mode', 'software')
# print(cam.__setattr__('trigger_mode', 'software'))

# print(cam.get_settings())
# raise ValueError

# cam.set_color_mode('rgb8p')
# print(cam.get_full_info())
# print(1/cam.get_exposure())
frame_rate = 1/cam.get_frame_period()
# define the number of frames
frame_buffer = 1000
total_frames = 100

# get the list of instruments
# cam = instrument('4103437084')
# print(list_instruments())
# print(cam)
# raise ValueError

# allocate memory for the frames
timestamp_list = []
compare_list = []
# get the reference time
ref_time = datetime.datetime.now()

fourcc = cv2.VideoWriter_fourcc(*'XVID')

out = cv2.VideoWriter('output.avi', fourcc, frame_rate, (1280, 1024))

# raise ValueError
# print(cam.get_settings(['trigger_mode']))
cam.setup_acquisition(nframes=frame_buffer)  # could be combined with start_acquisition, or kept separate
cam.start_acquisition()
# while True:  # acquisition loop
for idx in np.arange(total_frames):
    # wait for the next available frame
    cam.wait_for_frame()
    # get the oldest frame in the buffer from the camera
    frame, info = cam.read_oldest_image(return_info=True)
    # frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    # write it to file
    # out.write(frame)

    # get the timestamp
    # now_time = datetime.datetime.now()
    # timestamp = (now_time-ref_time).total_seconds()
    # ref_time = now_time
    tstamp = info[2]

    tstamp = datetime.datetime(year=tstamp[0], month=tstamp[1], day=tstamp[2], hour=tstamp[3], minute=tstamp[4],
                               second=tstamp[5], microsecond=tstamp[6]*1000)

    compare_list.append((tstamp, datetime.datetime.now()))
    if idx == 0:
        ref_time = tstamp
    else:
        new_time = tstamp
        timestamp_list.append((new_time-ref_time).total_seconds())
        ref_time = new_time

timestamp_list = [np.mean(timestamp_list)] + timestamp_list
# print(frame.shape)
out.release()
cam.stop_acquisition()
# close the camera
cam.close()

# get the frame times
frame_times = 1/(np.array(timestamp_list))
fig = plt.figure()
ax1 = fig.add_subplot(211)
ax1.hist(frame_times)
ax2 = fig.add_subplot(212)
ax2.plot(timestamp_list)

compare_list = np.array(compare_list)
fig2 = plt.figure()
plt.plot(compare_list[:, 0], compare_list[:, 1])

plt.show()
