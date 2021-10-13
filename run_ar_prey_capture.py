import subprocess
import paths
import datetime
from functions_recorder import initialize_projector, record_vr_rig, plot_inputs_vr, load_csv
from functions_osc import create_and_send
from os.path import join
from time import sleep
from functions_GUI import get_filename_suffix, replace_name_part


# configure recording
exp_type = 'ARPrey'

# unity experiment type
unity_path = paths.unityARPrey_camo_path

# initialize projector
my_device = initialize_projector()

# assemble the main body of the file name
time_name = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

# get and format the current time
# csvName = join(paths.bonsai_out, datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + r'_miniscope.csv')
csvName = join(paths.vr_path, time_name + '_' + exp_type + r'_suffix.csv')
videoName = csvName.replace('.csv', '.avi')

# launch bonsai tracking
bonsai_process = subprocess.Popen([paths.bonsai_path, paths.bonsaiworkflow_path,
                                   "-p:csvName="""+csvName+"""""",
                                   "-p:videoName="""+videoName+"""""",
                                   "--start"])
sleep(2)
# launch Unity
unity_process = subprocess.Popen([unity_path])

# start recording
duration, current_path_sync = record_vr_rig(my_device, paths.vr_path, time_name, exp_type)

# close the opened applications
create_and_send(paths.bonsai_ip, paths.bonsai_port, paths.bonsai_address, [1])
create_and_send(paths.unity_ip, paths.unity_in_port, paths.unity_address, [1])

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
