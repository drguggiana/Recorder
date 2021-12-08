import time
import os
import csv
import keyboard
import nidaqmx as ni
import matplotlib.pyplot as plt
import numpy as np
import functions_osc_python3 as osc
import paths


def plot_inputs_miniscope(frame_list):
    """Plot the sync data"""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax1, = ax.plot(frame_list[:, 0], frame_list[:, 1], marker='o')
    ax2, = ax.plot(frame_list[:, 0], frame_list[:, 2] + 2, marker='o')
    ax3, = ax.plot(frame_list[:, 0], frame_list[:, 3] + 4, marker='o')
    ax.legend((ax1, ax2, ax3), ('Miniscope', 'Camera', 'Sync_trigger'))
    plt.show()


def load_csv(path):
    """Load csv data from a file path"""
    with open(path) as f:
        csv_reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        frame_list = [row for row in csv_reader]
    return np.array(frame_list)


def record_miniscope_ni(path_in, name_in, device='Dev1'):
    """Write the sync data to a text file"""
    # allocate a list to store the frames
    t_start = time.perf_counter()

    # define the file to save the path to
    file_name = os.path.join(path_in, name_in + '_syncMini_suffix.csv')

    # open the file
    with open(file_name, mode='w', newline='') as f:
        # initialize the writer
        f_writer = csv.writer(f, delimiter=',')
        with ni.Task() as task:
            # create the tasks
            task.ai_channels.add_ai_voltage_chan(device+'/ai0:1')

            # wait for the camera
            osc.create_blocking_server(paths.recorder_ip, paths.recorder_port, '/close')
            # initialize a line counter
            line_counter = 0
            # initialize a terminator counter
            end_counter = 100
            # for several frames
            while True:
                # read from the DAQ
                miniscope_trigger, cam_trigger = task.read()
                # set the trigger
                sync_trigger = 0

                # after 100 reads, start the camera acquisition
                if line_counter == 100:
                    sync_trigger = 1
                    osc.create_send_close(paths.cam_ip, paths.cam_port, '/cam_loop', [1])

                # get the timestamp
                t = time.perf_counter() - t_start
                # write to the file
                f_writer.writerow([t, miniscope_trigger, cam_trigger, sync_trigger])

                # update the counter
                line_counter += 1

                if keyboard.is_pressed('Escape'):
                    # kill the camera process
                    osc.create_send_close(paths.cam_ip, paths.cam_port, '/cam_loop', [0])
                    end_counter -= 1
                if (end_counter < 100) & (end_counter > 0):
                    end_counter -= 1
                elif end_counter <= 0:
                    break

    return 'Total duration: ' + str(time.perf_counter() - t_start), file_name
