from pypixxlib.propixx import PROPixxCTRL, PROPixx
import numpy as np
import time
import matplotlib.pyplot as plt
import pypixxlib._libdpx as libd
import keyboard


# get the device object for the controller
my_device = PROPixxCTRL()
# enable pixel mode
libd.DPxEnableDoutPixelMode()
# libd.DPxDisableDoutPixelMode()

# libd.DPxSetMarker()
# libd.DPxWriteRegCacheAfterVideoSync()

# allocate a list to store the frames
frame_list = []
t_start = time.time()
my_device.updateRegisterCache()
# libd.DPxUpdateRegCacheAfterVideoSync()

# proj_start = libd.DPxGetMarker()
# libd.DPxSetMarker()
# libd.DPxWriteRegCacheAfterVideoSync()

# for several frames
# for frames in np.arange(number_frames):
while True:
    my_device.updateRegisterCache()
    # libd.DPxUpdateRegCacheAfterVideoSync()
    din_state = my_device.din.getValue()
    proj_trigger = din_state & 2**10
    bonsai_trigger = din_state & 2**4
    miniscope_trigger = din_state & 2**6
    optitrack_trigger = din_state & 2**2

    t = time.time() - t_start
    # proj_marker = libd.DPxGetMarker()
    # if proj_marker != proj_start:
    #     proj_trigger = 5
    #     libd.DPxSetMarker()
    #     # libd.DPxWriteRegCacheAfterVideoSync()
    #
    #     proj_start = proj_marker
    # else:
    #     proj_trigger = 0

    frame_list.append([t, proj_trigger, bonsai_trigger, miniscope_trigger, optitrack_trigger])
    if keyboard.is_pressed('Escape'):
        break

# turn the list into an array
frame_list = np.array(frame_list)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(frame_list[:, 0], frame_list[:, 1], marker='o')
ax.plot(frame_list[:, 0], frame_list[:, 2], marker='o')
# ax.plot(frame_list[:, 0], frame_list[:, 3], marker='o')
# ax.plot(frame_list[:, 0], frame_list[:, 4], marker='o')
plt.show()
