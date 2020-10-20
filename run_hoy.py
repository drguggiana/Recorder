import subprocess
import datetime
from os.path import join
from time import sleep
from itertools import product
from random import sample
import pandas as pd

import paths
# from functions_osc import create_and_send, create_server
# from functions_recorder import initialize_projector, record_vr_rig, plot_inputs_vr, load_csv
# from functions_GUI import get_filename_suffix, replace_name_part


# -- configure recording -- #
# initialize projector
# my_device = initialize_projector()

# assemble the main body of the file name
time_name = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

# get and format the current time
csvName = join(paths.bonsai_out, time_name + r'_suffix.csv')
videoName = csvName.replace('.csv', '.avi')

# -- Load experiment parameters from excel file -- #

# This is the parameter row that you want to use (1-indexed to match excel)
parameter_set = 1

# Load the file
all_params = pd.read_excel(paths.hoy_params_path, header=0, dtype=object)
session_params = all_params.loc[[parameter_set - 1]]

# Create a set of all trial permutations
temp_trials = [eval(session_params[col][0]) for col in session_params.columns[:-3]]
trial_permutations = list(product(*temp_trials))

# Generate repeats
reps = session_params['repetitions'][0]
trial_permutations = [trial for trial in trial_permutations for i in range(reps)]

# Randomly shuffles all trial permutations
trial_permutations = sample(trial_permutations, len(trial_permutations))
trials = pd.DataFrame(trial_permutations, columns=session_params.columns[:-3])

# If we want to only shuffle by certain parameters and keep others constant or
# monotonically increasing, check that here
sortby = eval(session_params['sortby'][0])
if type(sortby) is list:
    trials = trials.sort_values(sortby, ascending=True)

# -- launch subprocesses and start recording -- #

# launch bonsai tracking
# bonsai_process = subprocess.Popen([paths.bonsai_path, paths.bonsaiworkflow_path,
#                                    "-p:csvName="""+csvName+"""""", "-p:videoName="""+videoName+"""""", "--start"])

# launch Unity tracking
# unity_process = subprocess.Popen([paths.unity_path])

# start recording
# duration, current_path_sync = record_vr_rig(my_device, paths.sync_path, time_name, '_syncVR')


# -- handle trial structure -- #
listener = create_server()
in_trial = False
for trial_num, row in trials.iterrows():
    # Generate a message to be sent via OSC client
    trial_message = ['/TrialStart', 0, *row.to_list()]
    in_trial = True

    # Send trial string to Unity
    # create_and_send(paths.unity_ip, paths.unity_port, paths.unity_address, trial_message)

    # Listen for the trial completed  message
    while in_trial:
        # Listen for the trial end

    print('hi')





# -- shutdown subprocesses and save -- #

# close the opened applications

# create_and_send(paths.bonsai_ip, paths.bonsai_port, paths.bonsai_address, [1])

sleep(2)
bonsai_process.kill()

# # plot the timing
#
# # load the frame_list
# print(duration)
#
# frame_list = load_csv(current_path_sync)
# plot_inputs_vr(frame_list)
#
# # ask the user for the suffix (animal, result, notes)
# suffix = get_filename_suffix()
#
# # add the suffix to all the file names
# file_list = [csvName, videoName, current_path_sync]
# failed_files = replace_name_part(file_list, 'suffix', suffix)
# print(failed_files)
#
# # do the same for the bonsai files
# unity_file = [paths.unity_temp_path]
# failed_unity = replace_name_part(unity_file, 'suffix', '_'.join((time_name, suffix)))
# print(failed_unity)
#
# print('hi')