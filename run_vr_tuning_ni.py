import pandas as pd
import subprocess
import datetime
import itertools
from os.path import join
from time import sleep
from random import sample
from math import isnan
from datetime import timedelta

import paths
from functions_GUI import get_filename_suffix, replace_name_part, replace_name_approx
from vr_experiment_structures import VRTuningTrialStructure
import functions_nidaq as fn
from functions_osc4py3 import OSCManager

# -- Initialize the OSC servers and clients -- #
unity_osc = OSCManager()
unity_osc.create_server(paths.unity_ip, paths.unity_out_port, 'server_recorder')
unity_osc.create_client(paths.unity_ip, paths.unity_in_port, 'client_unity')
unity_osc.create_client(paths.unity_ip, paths.cam_port, 'client_cam')

# -- configure recording -- #
exp_type = paths.exp_type

# unity experiment type
unity_path = paths.unityVRTuning_path

# initialize projector
my_device = fn.initialize_projector()

# get and format the current time
time_name = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

# assemble the main body of the file name
videoName = join(paths.vr_path, time_name + '_' + exp_type + r'_suffix.avi')
trialsetName = videoName.replace('.avi', '.h5')

# -- Load experiment parameters from excel file -- #

# This is the parameter row that you want to use (matches excel row number)
parameter_set = paths.parameter_set

# Load the file
all_params = pd.read_excel(paths.vrTuning_params_path, header=0, dtype=object)
session_params = all_params.loc[[parameter_set - 2]]
session_params.reset_index(inplace=True, drop=True)

# Get trial duration
trial_duration = float(session_params['trial_duration'][0])
if isnan(trial_duration):
    trial_duration = 2.0

# Get number of repetitions
repetitions = int(session_params['repetitions'][0])
if isnan(repetitions):
    repetitions = 1

# Get inter-stim interval
isi = float(session_params['isi'][0])
if isnan(isi):
    isi = 1.0

# Create a set of all trial permutations
valid_cols = session_params.columns.get_loc('trial_duration')
temp_trials = [eval(session_params[col][0]) for col in session_params.columns[:valid_cols]]
trial_permutations = list(itertools.product(*temp_trials))
trial_permutations = list(itertools.chain.from_iterable(itertools.repeat(x, repetitions) for x in trial_permutations))

# Randomly shuffle all trial permutations
trial_permutations = sample(trial_permutations, len(trial_permutations))
trials = pd.DataFrame(trial_permutations, columns=session_params.columns[:valid_cols], dtype=float)

# If we want to only shuffle by certain parameters and keep others constant or
# monotonically increasing, check that here
try:
    sortby = eval(session_params['sortby'][0])
    if type(sortby) is list:
        trials = trials.sort_values(sortby, ascending=True)
        trials.reset_index(inplace=True, drop=True)
except TypeError:
    pass

# Put all of this in a class to be processed
session = VRTuningTrialStructure(trials, trial_duration, isi)


# -- launch subprocesses and start recording -- #
print('Beginning session... {} trials in total.\nApprox. session duration: {} \n'.format(len(trials),
                                                                                         timedelta(seconds=session.duration)))
# launch the camera software
camera_process = subprocess.Popen(['python', paths.cam_path, paths.vr_cam_serials[exp_type], videoName])

# launch Unity
unity_process = subprocess.Popen([unity_path])
# sleep(4)

# start recording
duration, current_path_sync = fn.record_vr_trial_experiment(session, paths.vr_path, time_name, exp_type, unity_osc)

# -- shutdown subprocesses -- #
print("End Session")

# Create the H5 file to store the params
with pd.HDFStore(trialsetName) as sess:
    sess['trial_set'] = trials
    sess['params'] = session_params

# close the opened applications
# create_and_send(paths.bonsai_ip, paths.bonsai_port, paths.bonsai_address, [1])
# create_and_send(paths.unity_ip, paths.unity_in_port, paths.unity_address, [1])
# unity_osc.send_message('client_unity', '/Close', [1])

camera_process.terminate()
camera_process.wait()
unity_process.terminate()
unity_process.wait()

unity_osc.stop()
# bonsai_process.kill()
# unity_process.kill()

# get the projector out of pixel mode
fn.restore_projector()
# -- save and rename files -- #

# ask the user for the suffix (animal, result, notes)
suffix = get_filename_suffix()

# add the suffix to all the file names
file_list = [videoName, trialsetName, current_path_sync]
failed_files, new_names = replace_name_part(file_list, 'suffix', suffix)
print(failed_files)

# move the unity/motive file to the target folder
unity_file = [paths.unity_temp_path]
failed_unity, new_unity_name = replace_name_part(unity_file, paths.unity_temp_path, join(paths.vr_path, 'suffix.txt'))
print(failed_unity)

# rename the unity/motive file to have the correct suffix
failed_unity, _ = replace_name_part(new_unity_name, 'suffix', '_'.join((time_name, exp_type, suffix)))
print(failed_unity)

# Rename the miniscope .tif file and move it to the target folder
# grab the csv path and change the extension
new_tif_name = new_names[0].replace('.avi', '.doric')
# TODO: test this functionality
# add the matching name to the miniscope file (grabbing the file with the closest creation time, within 100 seconds)
replace_name_approx(paths.doric_path, new_names[0], new_tif_name, threshold=100, extension='.doric')

# -- plot the timing -- #

# load the frame_list
print(duration)
frame_list = fn.load_csv(new_names[2])

# get the frames for the camera
framerate, frame_number, _, _ = fn.calculate_frames(frame_list, 2)
print(f'Number of camera frames: {frame_number}')
print(f'Effective camera framerate: {framerate}')

# get the frames for unity
framerate, frame_number, _, _ = fn.calculate_frames(frame_list, 1, column_type='projector')
print(f'Number of unity frames: {frame_number}')
print(f'Effective unity framerate: {framerate}')

# get the frames for the miniscope
# TODO: revise this part
framerate, frame_number, _, _ = fn.calculate_frames(frame_list, 4)
print(f'Number of miniscope frames: {frame_number}')
print(f'Effective miniscope framerate: {framerate}')

fn.plot_inputs_vr(frame_list)
