import time
import os
import csv
import keyboard
import nidaqmx as ni
import matplotlib.pyplot as plt
import numpy as np
# import functions_osc_python3 as osc
from functions_osc4py3 import OSCManager
import paths
from datetime import timedelta


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
                    osc.simple_send('client_cam', '/simple_read', 1)

                # get the timestamp
                t = time.perf_counter() - t_start
                # write to the file
                f_writer.writerow([t, miniscope_trigger, cam_trigger, sync_trigger])

                # update the counter
                line_counter += 1

                if keyboard.is_pressed('Escape'):
                    # kill the camera process
                    # osc.create_send_close(paths.cam_ip, paths.cam_port, '/cam_loop', [0])
                    osc.simple_send('client_cam', '/simple_read', 2)
                    end_counter -= 1
                if (end_counter < 100) & (end_counter > 0):
                    end_counter -= 1
                elif end_counter <= 0:
                    break
    # terminate the osc
    osc.stop()
    return 'Total duration: ' + str(time.perf_counter() - t_start), file_name


def record_vr_trial_experiment(session, path_in, name_in, exp_type):
    """Handle the trial communication structure and write the sync data to a text file"""

    # define the file to save the path to
    file_name = os.path.join(path_in, name_in + "_sync" + exp_type + '_suffix.csv')

    # my_device.updateRegisterCache()

    # launch OSC server with Unity
    unity_osc = osc.create_server(paths.unity_ip, paths.unity_out_port)
    # Create thread/socket to listen
    unity_sock = unity_osc.listen(address=paths.unity_ip, port=paths.unity_out_port, default=True)

    # Triggers a callback to the 'unity_ready' function
    unity_osc.bind(b'/UnityReady', session.unity_ready, sock=unity_sock)

    # Triggers a callback to the 'received_trial' function
    unity_osc.bind(b'/TrialReceived', session.received_trial, sock=unity_sock)

    # The EndTrial message triggers a callback to the 'end_trial' function
    unity_osc.bind(b'/EndTrial', session.end_trial, sock=unity_sock)

    # my_device.updateRegisterCache()

    # Send the setup instructions to Unity
    print('Setting up experiment...')
    setup_message = session.assemble_setup_message()
    unity_osc.send_message(b'/SetupExperiment', setup_message, paths.unity_ip, paths.unity_in_port, sock=unity_sock)

    # open the file
    with open(file_name, mode='w') as f:
        # initialize the writer
        f_writer = csv.writer(f, delimiter=',')

        t_start = time.time()

        # for several frames
        while session.in_experiment:
            # my_device.updateRegisterCache()
            # din_state = my_device.din.getValue()
            # proj_trigger = (din_state & 2 ** 10 + 1) / (2 ** 10 + 1)
            # bonsai_trigger = (din_state & 2 ** 4 + 1) / (2 ** 4 + 1)
            # optitrack_trigger = (din_state & 2 ** 6 + 1) / (2 ** 6 + 1)
            # miniscope_trigger = (din_state & 2 ** 2 + 1) / (2 ** 2 + 1)

            t = time.time() - t_start

            # write to the file
            f_writer.writerow([t, proj_trigger, bonsai_trigger, optitrack_trigger, miniscope_trigger])

            if session.ready:

                if not session.is_started:
                    # Send a message to unity to begin the session
                    print('Starting session...\n')
                    unity_osc.send_message(b'/SessionStart', [""], paths.unity_ip, paths.unity_in_port, sock=unity_sock)
                    session.is_started = True

                # Process the OSC communication - trial structure is handled by Unity
                if session.setup_trial:
                    # Reset setup trial bool
                    session.setup_trial = False

                    # Generate a message to be sent via OSC client
                    message = session.assemble_trial_message()

                    # Send trial string to Unity
                    print('Trial {} sent'.format(message[0]))
                    print(message)
                    unity_osc.send_message(b'/SetupTrial', message, paths.unity_ip, paths.unity_in_port, sock=unity_sock)

                    # Received OSC messages are automatically picked up by a separate thread
                    # session.end_trial is called buy the OSC listener automatically. It increments to the next trial
                    # and resets the session.start_trial boolean

            if keyboard.is_pressed('Escape'):
                break

    unity_osc.stop_all()
    unity_osc.terminate_server()
    return 'Total duration: ' + str(timedelta(seconds=(time.time() - t_start))), file_name
