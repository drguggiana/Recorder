from pypixxlib.propixx import PROPixxCTRL, PROPixx
import numpy as np
import time
import matplotlib.pyplot as plt
import pypixxlib._libdpx as libd
import keyboard
from datetime import datetime
import csv
import os.path


def initialize_projector():
    """Initialize the projector controller"""
    # get the device object for the controller
    my_device = PROPixxCTRL()
    # enable pixel mode
    libd.DPxEnableDoutPixelMode()
    return my_device

# libd.DPxDisableDoutPixelMode()

# libd.DPxSetMarker()
# libd.DPxWriteRegCacheAfterVideoSync()


def record_inputs_frames(my_device, number_frames):
    """Record a given number of samples from the Propixx controller to a list"""
    # allocate a list to store the frames
    frame_list = []
    t_start = time.time()
    my_device.updateRegisterCache()

    # for several frames
    for frames in np.arange(number_frames):
        my_device.updateRegisterCache()
        din_state = my_device.din.getValue()
        proj_trigger = din_state & 2**10
        bonsai_trigger = din_state & 2**4
        miniscope_trigger = din_state & 2**6
        optitrack_trigger = din_state & 2**2

        t = time.time() - t_start

        frame_list.append([t, proj_trigger, bonsai_trigger, miniscope_trigger, optitrack_trigger])

    # turn the list into an array
    frame_list = np.array(frame_list)

    return frame_list


def record_inputs_key(my_device):
    """Record sync data on a list until escape is pressed"""
    # allocate a list to store the frames
    frame_list = []
    t_start = time.time()
    my_device.updateRegisterCache()

    # for several frames
    while True:
        my_device.updateRegisterCache()
        din_state = my_device.din.getValue()
        proj_trigger = (din_state & 2**10 + 1)/(2**10 + 1)
        bonsai_trigger = (din_state & 2**4 + 1)/(2**4 + 1)
        miniscope_trigger = (din_state & 2**6 + 1)/(2**6 + 1)
        optitrack_trigger = (din_state & 2**2 + 1)/(2**2 + 1)

        t = time.time() - t_start

        frame_list.append([t, proj_trigger, bonsai_trigger, miniscope_trigger, optitrack_trigger])
        if keyboard.is_pressed('Escape'):
            break

    # turn the list into an array
    frame_list = np.array(frame_list)

    return frame_list


def record_vr_rig(my_device, path_in):
    """Write the sync data to a text file"""
    # allocate a list to store the frames
    # frame_list = []
    t_start = time.time()
    my_device.updateRegisterCache()

    # define the file to save the path to
    file_name = os.path.join(path_in, datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + '_syncVR.csv')
    # open the file
    with open(file_name, mode='w') as f:
        # initialize the writer
        f_writer = csv.writer(f, delimiter=',')
        # for several frames
        while True:
            my_device.updateRegisterCache()
            din_state = my_device.din.getValue()
            proj_trigger = (din_state & 2**10 + 1)/(2**10 + 1)
            bonsai_trigger = (din_state & 2**4 + 1)/(2**4 + 1)
            optitrack_trigger = (din_state & 2**6 + 1)/(2**6 + 1)
            miniscope_trigger = (din_state & 2**2 + 1)/(2**2 + 1)

            t = time.time() - t_start

            # write to the file
            f_writer.writerow([t, proj_trigger, bonsai_trigger, optitrack_trigger, miniscope_trigger])
            if keyboard.is_pressed('Escape'):
                break

    return 'Total duration: ' + str(time.time() - t_start), file_name


def record_miniscope_rig(my_device, path_in, name_in):
    """Write the sync data to a text file"""
    # allocate a list to store the frames
    # frame_list = []
    t_start = time.time()
    my_device.updateRegisterCache()

    # define the file to save the path to
    # file_name = os.path.join(path_in, datetime.now().strftime("%d_%m_%Y_%H_%M_%S") + '_syncMini.csv')
    file_name = os.path.join(path_in, name_in + '_syncMini_suffix.csv')
    # open the file
    with open(file_name, mode='w') as f:
        # initialize the writer
        f_writer = csv.writer(f, delimiter=',')
        # for several frames
        while True:
            my_device.updateRegisterCache()
            din_state = my_device.din.getValue()
            miniscope_trigger = (din_state & 2**2 + 1)/(2**2 + 1)
            bonsai2_trigger = (din_state & 2**8 + 1)/(2**8 + 1)

            t = time.time() - t_start

            # write to the file
            f_writer.writerow([t, miniscope_trigger, bonsai2_trigger])
            if keyboard.is_pressed('Escape'):
                break

    return 'Total duration: ' + str(time.time() - t_start), file_name


def plot_inputs_vr(frame_list):
    """Plot the sync data"""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax1, = ax.plot(frame_list[:, 0], frame_list[:, 1], marker='o')
    ax2, = ax.plot(frame_list[:, 0], frame_list[:, 2] + 2, marker='o')
    ax3, = ax.plot(frame_list[:, 0], frame_list[:, 3] + 4, marker='o')
    ax4, = ax.plot(frame_list[:, 0], frame_list[:, 4] + 6, marker='o')
    ax.legend((ax1, ax2, ax3, ax4), ('Projector', 'Bonsai', 'Optitrack', 'Miniscope'))
    plt.show()


def plot_inputs_miniscope(frame_list):
    """Plot the sync data"""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax1, = ax.plot(frame_list[:, 0], frame_list[:, 1], marker='o')
    ax2, = ax.plot(frame_list[:, 0], frame_list[:, 2] + 2, marker='o')
    ax.legend((ax1, ax2), ('Miniscope', 'Bonsai'))
    plt.show()


def load_csv(path):
    """Load csv data from a file path"""
    with open(path) as f:
        csv_reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        frame_list = [row for row in csv_reader]
    return np.array(frame_list)
