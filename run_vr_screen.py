import subprocess
import datetime
from os.path import join
from time import sleep
from itertools import product
from random import sample
import pandas as pd
from math import isnan
from datetime import timedelta

import paths
from functions_osc import create_and_send
from functions_recorder import VRScreenTrialStructure, initialize_projector, record_vr_screen_rig, plot_inputs_vr, load_csv
from functions_GUI import get_filename_suffix, replace_name_part


# -- configure recording -- #
exp_type = 'VScreen'

# initialize projector
my_device = initialize_projector()

# assemble the main body of the file name
time_name = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

# get and format the current time
# csvName = join(paths.bonsai_out, datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + r'_miniscope.csv')
csvName = join(paths.vr_path, time_name + '_' + exp_type + r'_suffix.csv')
videoName = csvName.replace('.csv', '.avi')
trialsetName = csvName.replace('.csv', '.h5')

# -- Load experiment parameters from excel file -- #

# This is the parameter row that you want to use (1-indexed to match excel)
parameter_set = 1

# Load the file
all_params = pd.read_excel(paths.vrscreen_params_path, header=0, dtype=object)
session_params = all_params.loc[[parameter_set - 1]]
session_params.reset_index(inplace=True, drop=True)

# Create a set of all trial permutations
# temp_trials = []
# for col in session_params.columns[:-4]:
#     par = eval(session_params[col][0])
#     if 'color' in col:
#         par = [str(p) for p in par]
#     temp_trials.append(par)
temp_trials = [eval(session_params[col][0]) for col in session_params.columns[:-4]]
trial_permutations = list(product(*temp_trials))

# Get inter-stim interval
isi = float(session_params['isi'][0])
if isnan(isi):
    isnan = 5.0

# Generate repeats
reps = int(session_params['repetitions'][0])
trial_permutations = [trial for trial in trial_permutations for i in range(reps)]

# Randomly shuffle all trial permutations
trial_permutations = sample(trial_permutations, len(trial_permutations))
trials = pd.DataFrame(trial_permutations, columns=session_params.columns[:-4])

# Put all of this in a class to be processed by
session = VRScreenTrialStructure(trials, isi)

# If we want to only shuffle by certain parameters and keep others constant or
# monotonically increasing, check that here
try:
    sortby = eval(session_params['sortby'][0])
    if type(sortby) is list:
        trials = trials.sort_values(sortby, ascending=True)
        trials.reset_index(inplace=True, drop=True)
except TypeError:
    pass

# Create the H5 file to store the params
with pd.HDFStore(trialsetName) as sess:
    sess['trial_set'] = trials
    sess['params'] = session_params

# -- launch subprocesses and start recording -- #

# launch bonsai tracking
bonsai_process = subprocess.Popen([paths.bonsai_path, paths.bonsaiworkflow_path,
                                   "-p:csvName="""+csvName+"""""", "-p:videoName="""+videoName+"""""", "--start"])

# launch Unity
unity_process = subprocess.Popen([paths.unityVRScreen_path])

sleep(10)

# start recording
print('Beginning session... {} trials in total. Session duration: {} '.format(len(trials),
                                                                              timedelta(seconds=session.duration)))

duration, current_path_sync = record_vr_screen_rig(session, my_device, paths.vr_path, time_name, exp_type)

# -- shutdown subprocesses -- #
print("End Session")

# close the opened applications

create_and_send(paths.bonsai_ip, paths.bonsai_port, paths.bonsai_address, [1])
create_and_send(paths.unity_ip, paths.unity_in_port, paths.unity_address, [1])

sleep(2)
bonsai_process.kill()
unity_process.kill()

# -- plot the timing -- #

# load the frame_list
print(duration)

frame_list = load_csv(current_path_sync)
plot_inputs_vr(frame_list)

# -- save and rename files -- #

# ask the user for the suffix (animal, result, notes)
suffix = get_filename_suffix()

# add the suffix to all the file names
file_list = [csvName, videoName, trialsetName, current_path_sync]
failed_files, _ = replace_name_part(file_list, 'suffix', suffix)
print(failed_files)

# do the same for the bonsai files
unity_file = [paths.unity_temp_path]
failed_unity, new_names = replace_name_part(unity_file, paths.unity_temp_path, join(paths.vr_path, 'suffix.txt'))
print(failed_unity)

failed_unity, _ = replace_name_part(new_names, 'suffix', '_'.join((time_name, exp_type, suffix)))
print(failed_unity)

# print('hi')