import nidaqmx as ni
import numpy as np
import matplotlib.pyplot as plt

import subprocess
import paths
import datetime
import functions_nidaq as fn
from os.path import join
from functions_GUI import get_filename_suffix, replace_name_part, replace_name_approx


# assemble the main body of the file name
time_name = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

# get and format the current time
videoName = join(paths.miniscope_path, time_name + r'_miniscope_suffix.avi')
# videoName = csvName.replace('.csv', '.avi')

# launch the camera software
camera_process = subprocess.Popen(['python', paths.cam_path, paths.cam_miniscope_serial, videoName])

# start recording
duration, current_path_sync = fn.record_miniscope_ni(paths.miniscope_path, time_name)

# terminate the camera process and wait until it fully dies
camera_process.terminate()
camera_process.wait()

# load the sync data just saved
frame_list = fn.load_csv(current_path_sync)

# print the duration of the experiment
print(duration)
# trim the list at the start frame
start_frame = np.argwhere(frame_list[:, 3] == 1)[0][0]
# get the effective camera framerate and print
frame_times = frame_list[np.argwhere(np.diff(np.round(frame_list[:, 1])) > 0).flatten()+1, 0]
# get the deltas between the start frame and the camera frames
delta_time = frame_list[start_frame, 0] - frame_times

# if the shutter was active during the start, still take it
if np.round(frame_list[start_frame, 1]) > 0:
    # find the first trigger before or at the start frame
    start_time = np.argwhere(delta_time >= 0)[-1][0]
else:
    # otherwise, find the first trigger after the start frame
    start_time = np.argwhere(delta_time > 0)[-1][0]

# trim the frame times and list accordingly
frame_times = frame_times[start_time:]
frame_list = frame_list[start_frame:, :]
# calculate the framerate
framerate = 1/np.mean(np.diff(frame_times))
print(f'Number of frames: {frame_times.shape[0]}')
print(f'Effective camera framerate: {framerate}')
# plot the sync data to make sure the triggers are fine
fn.plot_inputs_miniscope(frame_list)


# ask the user for the suffix (animal, result, notes)
suffix = get_filename_suffix()

# add the suffix to all the file names
file_list = [videoName, current_path_sync]
failed_files, new_names = replace_name_part(file_list, 'suffix', suffix)
print(failed_files)

# grab the csv path and change the extension
new_tif_name = new_names[0].replace('.avi', '.tif')
# TODO: test this functionality
# add the matching name to the miniscope file (grabbing the file with the closest creation time, within 100 seconds)
replace_name_approx(paths.doric_path, new_names[0], new_tif_name, threshold=100, extension='.tif')

