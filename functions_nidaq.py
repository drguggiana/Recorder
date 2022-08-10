import time
import os
import csv
import keyboard
import nidaqmx as ni
import matplotlib.pyplot as plt
import numpy as np
from functions_osc4py3 import OSCManager
import paths
from datetime import timedelta
from pypixxlib.propixx import PROPixxCTRL, PROPixx
# import pypixxlib._libdpx as libd
from pypixxlib import digitalOut


def normalize_row(row_in):
    """Simple function to normalize the triggers before plotting"""
    row_out = (row_in - row_in.min())/(row_in.max() - row_in.min())
    return row_out


def initialize_projector():
    """Initialize the projector controller"""
    # get the device object for the controller
    my_device = PROPixxCTRL()
    # enable pixel mode
    # libd.DPxEnableDoutPixelMode()
    dout = digitalOut.DigitalOut()
    dout.enablePixelMode()
    return my_device


def restore_projector():
    """Disable pixel mode"""
    dout = digitalOut.DigitalOut()
    dout.disablePixelMode()
    return


def plot_inputs_miniscope(frame_list):
    """Plot the sync data"""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax1, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 1]), marker='o')
    ax2, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 2]) + 2, marker='o')
    ax3, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 3]) + 4, marker='o')
    ax.legend((ax1, ax2, ax3), ('Miniscope', 'Camera', 'Sync_trigger'))
    plt.show()


def plot_inputs_vr(frame_list):
    """Plot the sync data"""
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax1, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 1]), marker='o')
    ax2, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 2]) + 2, marker='o')
    ax3, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 3]) + 4, marker='o')
    ax4, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 4]) + 6, marker='o')
    ax5, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 5]) + 8, marker='o')
    ax6, = ax.plot(frame_list[:, 0], normalize_row(frame_list[:, 6]), marker='o')
    ax.legend((ax1, ax2, ax3, ax4, ax5, ax6), ('Projector', 'Camera', 'Sync', 'Miniscope',
                                               'Wheel', 'Projector 2'))
    plt.show()


def calculate_frames(frame_list, target_column, time_column=0, sync_column=3, column_type=None):
    """Determine the number of recorded frames and effective frame rates"""
    # trim the list at the start frame
    start_frame = np.argwhere(frame_list[:, sync_column] == 1)[0][0]
    stop_frame = np.argwhere(frame_list[:, sync_column] == 2)[0][0]
    # get the frame times of the target column
    if column_type == 'projector':
        frame_times = \
            frame_list[np.argwhere(np.abs(np.diff(np.round(frame_list[:, target_column]/2))) > 0).flatten()+1, 0]
    else:
        frame_times = frame_list[np.argwhere(np.diff(np.round(frame_list[:, target_column])) > 0).flatten()+1, 0]
    # if it's empty, return nan
    if len(frame_times) == 0:
        return np.nan, np.nan, np.nan, np.nan
    # get the deltas between the start frame and the camera frames
    delta_start = frame_list[start_frame, time_column] - frame_times

    # if the shutter was active during the start, still take it
    if np.round(frame_list[start_frame, target_column]) > 0:
        # find the first trigger before or at the start frame
        start_time = np.argwhere(delta_start >= 0)[-1][0]
    else:
        # otherwise, find the first trigger after the start frame
        start_time = np.argwhere(delta_start < 0)[0][0]

    # get the time of the last frame
    delta_stop = frame_list[stop_frame, time_column] - frame_times
    # it'll be the first trigger after the stop signal
    stop_time = np.argwhere(delta_stop >= 0)[-1][0]

    # trim the frame times and list accordingly
    frame_times = frame_times[start_time:stop_time+1]
    # calculate the framerate
    framerate = 1/np.mean(np.diff(frame_times))
    frame_number = frame_times.shape[0]

    return framerate, frame_number, start_frame, stop_frame


def load_csv(path):
    """Load csv data from a file path"""
    with open(path) as f:
        csv_reader = csv.reader(f, delimiter=',', quoting=csv.QUOTE_NONNUMERIC)
        frame_list = [row for row in csv_reader]
    return np.array(frame_list)


def detect_trigger(task_in, channel, threshold=3):
    """wait on an infinite loop for a trigger to be detected in the selected input channel according to the specified
    threshold"""
    while True:
        # read the values from the analog in
        values = task_in.read()
        # select the target value
        target_value = values[channel]
        # evaluate if it passes threshold
        if target_value > threshold:
            break
        if keyboard.is_pressed('Escape'):
            break
        # pause for next iteration
        time.sleep(0.01)
    return


def record_miniscope_ni(path_in, name_in, device='Dev1'):
    """Write the sync data to a text file"""
    # get the startup time
    t_start = time.perf_counter()

    # initialize the osc class
    osc = OSCManager()
    # define the servers to use
    osc.create_server(paths.recorder_ip, paths.recorder_port, 'server_recorder')
    osc.create_client(paths.cam_ip, paths.cam_port, 'client_cam')

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
            osc.wait_for_message('cam')
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
                    # osc.create_send_close(paths.cam_ip, paths.cam_port, '/cam_loop', [1])
                    osc.simple_send('client_cam', '/SimpleRead', 1)

                if keyboard.is_pressed('Escape'):
                    # kill the camera process
                    osc.simple_send('client_cam', '/SimpleRead', 2)
                    # signal the off trigger
                    sync_trigger = 2
                    # start the end counter
                    end_counter -= 1
                if (end_counter < 100) & (end_counter > 0):
                    end_counter -= 1
                elif end_counter <= 0:
                    break

                # get the timestamp
                t = time.perf_counter() - t_start
                # write to the file
                f_writer.writerow([t, miniscope_trigger, cam_trigger, sync_trigger])

                # update the counter
                line_counter += 1

    # terminate the osc
    osc.stop()
    return 'Total duration: ' + str(time.perf_counter() - t_start), file_name


def record_vr_trial_experiment(session, path_in, name_in, exp_type, unity_osc, device='Dev1'):
    """Handle the trial communication structure and write the sync data to a text file"""

    # define the file to save the path to
    file_name = os.path.join(path_in, name_in + "_sync" + exp_type + '_suffix.csv')

    # Triggers a callback to the 'received_trial' function
    unity_osc.bind('/TrialReceived', session.received_trial)

    # The EndTrial message triggers a callback to the 'end_trial' function
    unity_osc.bind('/EndTrial', session.end_trial)

    # open the file
    with open(file_name, mode='w', newline='') as f:
        # initialize the writer
        f_writer = csv.writer(f, delimiter=',')

        t_start = time.time()
        with ni.Task() as task, ni.Task() as task2:
            # create the tasks
            if exp_type in ['VWheel', 'VWheelWF']:
                task.ai_channels.add_ai_voltage_chan(device+'/ai2')
                task.ai_channels.add_ai_voltage_chan(device+'/ai7')
                task.ai_channels.add_ai_voltage_chan(device+'/ai4:6')
            else:
                task.ai_channels.add_ai_voltage_chan(device+'/ai2:6')
            # create the write task to control the miniscope
            task2.do_channels.add_do_chan('Dev1/port1/line0')

            # wait for the camera
            unity_osc.wait_for_message('device')
            unity_osc.wait_for_message('device')

            # check for the wirefree flag
            if 'WF' in exp_type:
                # hold execution until the PD is detected
                # TODO: define the threshold empirically
                detect_trigger(task, 3, threshold=3)
                # record the trigger
                t = time.time() - t_start
                f_writer.writerow([t, 0, 0, 0, 1, 0, 0])
                # print a message
                print('Photodiode trigger detected')
            # release unity
            unity_osc.send_message('client_unity', '/ReleaseWait', [0])
            # initialize a frame counter
            line_counter = 0
            # initialize the end counter
            end_counter = 1000

            # for several frames
            while True:
                # set the trigger
                sync_trigger = 0

                # trigger the start of the whole experiment after 100 frames
                if line_counter == 100:
                    # start the camera
                    unity_osc.simple_send('client_cam', '/SimpleRead', 1)
                    # signal unity to start the actual trial
                    unity_osc.send_message('client_unity', '/SessionStart', [0])
                    # start the miniscope
                    task2.write(True)
                    # signal the trigger in the sync file
                    sync_trigger = 1
                    print('Start sent')
                    session.setup_trial = True

                # Process the OSC communication - trial structure is handled by Unity
                if session.setup_trial:
                    # Reset setup trial bool
                    session.setup_trial = False

                    # Generate a message to be sent via OSC client
                    message = session.assemble_trial_message()

                    # Send trial string to Unity
                    print('Trial {} sent'.format(message[0]))
                    print(message)
                    unity_osc.send_message('client_unity', '/SetupTrial', message)

                    # Received OSC messages are automatically picked up by a separate thread
                    # and resets the session.start_trial boolean

                if (keyboard.is_pressed('Escape')) | (session.in_experiment is False):
                    # signal off trigger
                    sync_trigger = 2
                    # signal the camera to stop
                    unity_osc.simple_send('client_cam', '/SimpleRead', 2)
                    # signal unity to stop
                    unity_osc.simple_send('client_unity', '/Close', 0)
                    # stop the miniscope
                    task2.write(False)
                    # start the end counter
                    end_counter -= 1
                if (end_counter < 1000) & (end_counter > 0):
                    end_counter -= 1
                elif end_counter <= 0:
                    break

                # read the DAQ
                proj_trigger, cam_trigger, miniscope_trigger, running_wheel, proj_trigger2 = task.read()
                t = time.time() - t_start

                # write to the file
                f_writer.writerow([t, proj_trigger, cam_trigger, sync_trigger, miniscope_trigger,
                                   running_wheel, proj_trigger2])
                # update the counter
                line_counter += 1

    return 'Total duration: ' + str(timedelta(seconds=(time.time() - t_start))), file_name
