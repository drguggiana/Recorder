import subprocess
import datetime
from os.path import join
from time import sleep
from itertools import product
from random import sample
import pandas as pd

import paths
from functions_osc import create_and_send, create_server
from functions_recorder import initialize_projector, record_vr_rig, plot_inputs_vr, load_csv
from functions_GUI import get_filename_suffix, replace_name_part


def end_trial(*values):
    if False in values:
        global in_trial
        in_trial = False


# -- configure recording -- #
exp_type = 'VR'

# initialize projector
my_device = initialize_projector()

# assemble the main body of the file name
time_name = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

# get and format the current time
# csvName = join(paths.bonsai_out, datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + r'_miniscope.csv')
csvName = join(paths.vr_path, time_name + '_' + exp_type + r'_suffix.csv')
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

# Randomly shuffle all trial permutations
trial_permutations = sample(trial_permutations, len(trial_permutations))
trials = pd.DataFrame(trial_permutations, columns=session_params.columns[:-3])

# If we want to only shuffle by certain parameters and keep others constant or
# monotonically increasing, check that here
sortby = eval(session_params['sortby'][0])
if type(sortby) is list:
    trials = trials.sort_values(sortby, ascending=True)

# -- launch subprocesses and start recording -- #

# launch bonsai tracking
bonsai_process = subprocess.Popen([paths.bonsai_path, paths.bonsaiworkflow_path,
                                   "-p:csvName="""+csvName+"""""", "-p:videoName="""+videoName+"""""", "--start"])

sleep(1)

# launch Unity
unity_process = subprocess.Popen([paths.unityVRPHoy_path])

# launch OSC servers with Unity and Bonsai
bonsai_osc = create_server()
bonsai_sock = bonsai_osc.listen(port=paths.bonsai_port, default=True)    # Create thread/socket to listen
unity_osc = create_server()
unity_sock = unity_osc.listen(port=paths.unity_port, default=True)    # Create thread/socket to listen
unity_osc.bind(b'/EndTrial', end_trial)    # The EndTrial message triggers a callback to the end_trial function

# start recording
duration, current_path_sync = record_vr_rig(my_device, paths.vr_path, time_name, exp_type)

# -- handle trial structure -- #
in_trial = False

for trial_num, row in trials.iterrows():
    # Generate a message to be sent via OSC client
    trial_message = [trial_num + 1] + row.to_list()
    in_trial = True

    # Send trial string to Unity
    unity_osc.send_message(b'/TrialStart', trial_message, paths.unity_ip, paths.unity_port)
    print('Start trial {}'.format(trial_num))

    # Listen for the trial completed  message
    while in_trial:
        # Listen for the trial end
        unity_osc.listen(address=b'/EndTrial', port=paths.unity_port)
        sleep(0.001)

    print("End Trial")
    print('hi')


# -- shutdown subprocesses and save -- #

# close the opened applications
unity_osc.send_message(paths.unity_address, [1], paths.unity_ip, paths.unity_port, sock=unity_sock)
unity_osc.stop_all()

bonsai_osc.send_message(paths.bonsai_address, [1], paths.bonsai_ip, paths.bonsai_port, sock=bonsai_sock)
bonsai_osc.stop_all()

sleep(2)
bonsai_process.kill()
unity_process.kill()

# plot the timing

# load the frame_list
print(duration)

frame_list = load_csv(current_path_sync)
plot_inputs_vr(frame_list)

# ask the user for the suffix (animal, result, notes)
suffix = get_filename_suffix()

# add the suffix to all the file names
file_list = [csvName, videoName, current_path_sync]
failed_files, _ = replace_name_part(file_list, 'suffix', suffix)
print(failed_files)

# do the same for the bonsai files
unity_file = [paths.unity_temp_path]
failed_unity, new_names = replace_name_part(unity_file, paths.unity_temp_path, join(paths.vr_path, 'suffix.txt'))
print(failed_unity)

failed_unity, _ = replace_name_part(new_names, 'suffix', '_'.join((time_name, exp_type, suffix)))
print(failed_unity)

# print('hi')