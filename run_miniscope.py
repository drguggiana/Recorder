import subprocess
import paths
import datetime
from functions_recorder import initialize_projector, record_miniscope_rig, plot_inputs_miniscope, load_csv
from functions_osc import create_and_send
from os.path import join
from time import sleep
from functions_GUI import get_filename_suffix, replace_name_part

# configure recording
# initialize projector
my_device = initialize_projector()

# assemble the main body of the file name
time_name = datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S")

# get and format the current time
# csvName = join(paths.bonsai_out, datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + r'_miniscope.csv')
csvName = join(paths.bonsai_out, time_name + r'_miniscope_suffix.csv')
videoName = csvName.replace('.csv', '.avi')

# launch bonsai tracking
bonsai_process = subprocess.Popen([paths.bonsai_path, paths.miniscopeworkflow_path,
                                   "-p:csvName="""+csvName+"""""", "-p:videoName="""+videoName+"""""", "--start"])

# start recording
duration, current_path_sync = record_miniscope_rig(my_device, paths.sync_path, time_name)

# close the opened applications
create_and_send(paths.bonsai_ip, paths.bonsai_port, paths.bonsai_address, [1])


sleep(2)
bonsai_process.kill()

# print the duration of the experiment
print(duration)
# plot the sync data to make sure the triggers are fine
frame_list = load_csv(current_path_sync)
plot_inputs_miniscope(frame_list)

# ask the user for the suffix (animal, result, notes)
suffix = get_filename_suffix()

# add the suffix to all the file names
file_list = [csvName, videoName, current_path_sync]
failed_files = replace_name_part(file_list, 'suffix', suffix)
print(failed_files)
