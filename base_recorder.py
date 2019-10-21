from pypixxlib.propixx import PROPixxCTRL, PROPixx
import numpy as np
import time
import matplotlib.pyplot as plt
import pypixxlib._libdpx as libd

# get the device object for the controller
my_device = PROPixxCTRL()
# projector = PROPixx()
# enable pixel mode
libd.DPxEnableDoutPixelMode()

# libd.DPxDisableDoutPixelMode()

# libd.DPxSetMarker()
# libd.DPxWriteRegCacheAfterVideoSync()


# allocate a list to store the frames
frame_list = []
t_start = time.time()
# libd.DPxSetMarker()
my_device.updateRegisterCache()
# t_start = libd.DPxGetMarker()

# for several frames
for frames in np.arange(10000):
    my_device.updateRegisterCache()
    din_state = my_device.din.getValue() & 2**13
    t = time.time() - t_start
    # t = libd.DPxGetMarker() - t_start
    # libd.DPxSetMarker()
    # t = libd.DPxGetVidVPeriod()
    frame_list.append([t, din_state])
    # print(din_state)

# turn the list into an array
frame_list = np.array(frame_list)

fig = plt.figure()
ax = fig.add_subplot(111)
ax.plot(frame_list[:, 0], frame_list[:, 1], marker='o')
plt.show()

print('yay')
