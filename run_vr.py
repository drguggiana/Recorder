import subprocess
import paths
import datetime
from functions_recorder import initialize_projector, record_vr_rig, plot_inputs_vr, load_csv
from functions_osc import create_and_send
from os.path import join
from time import sleep

# configure recording
# initialize projector
my_device = initialize_projector()

# get and format the current time
csvName = join(paths.bonsai_out, datetime.datetime.now().strftime("%m_%d_%Y_%H_%M_%S") + r'.csv')
videoName = csvName.replace('.csv', '.avi')
# launch bonsai tracking
bonsai_process = subprocess.Popen([paths.bonsai_path, paths.bonsaiworkflow_path,
                                   "-p:csvName="""+csvName+"""""", "-p:videoName="""+videoName+"""""", "--start"])

# launch Unity tracking
unity_process = subprocess.Popen([paths.unity_path])

# start recording
duration, current_path_sync = record_vr_rig(my_device, paths.sync_path)

# close the opened applications
create_and_send(paths.bonsai_ip, paths.bonsai_port, paths.bonsai_address, [1])

create_and_send(paths.unity_ip, paths.unity_port, paths.unity_address, [1])

sleep(2)
bonsai_process.kill()

# plot the timing

# load the frame_list
print(duration)

frame_list = load_csv(current_path_sync)
plot_inputs_vr(frame_list)

