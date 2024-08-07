import os
import paths
import datetime
import shutil

import ffmpeg
import numpy as np
import pandas as pd
from skimage import io
from matplotlib import pyplot as plt


def delete_contents(folder_path):
    """Delete all files and folders inside the target folder
    taken from https://stackoverflow.com/questions/185936/how-to-delete-the-contents-of-a-folder and
    the prey_capture repo"""

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def load_avi(file_name):
    """Load an avi video from the wirefree miniscope (based on minian code)"""
    # get the file info
    info = ffmpeg.probe(file_name)
    video_info = next(s for s in info["streams"] if s["codec_type"] == "video")
    w = int(video_info["width"])
    h = int(video_info["height"])
    f = int(video_info["nb_frames"])
    # load the file
    out_bytes, err = (
        ffmpeg.input(file_name)
        .video.output("pipe:", format="rawvideo", pix_fmt="gray")
        .run(capture_stdout=True)
    )
    stack_out = np.frombuffer(out_bytes, np.uint8).reshape(f, h, w).copy()
    # get rid of the 0 frames
    keep_idx = np.sum(np.sum(stack_out, axis=2), axis=1) != 0
    stack_out = stack_out[keep_idx, :, :]
    return stack_out


def concatenate_wirefree_video(filenames, processing_path=None):
    """Concatenate the videos from a single recording into a single tif file"""
    # based on https://stackoverflow.com/questions/47182125/how-to-combine-tif-stacks-in-python

    # read the first stack on the list
    im_1 = load_avi(filenames[0])

    # save the file name and the number of frames
    frames_list = [[filenames[0], im_1.shape[0]]]
    # assemble the output path
    if processing_path is not None:
        # get the basename
        base_name = os.path.basename(filenames[0])
        out_path_tif = os.path.join(processing_path, base_name.replace('.avi', '_CAT.tif'))
        out_path_log = os.path.join(processing_path, base_name.replace('.avi', '_CAT.csv'))
    else:
        out_path_tif = filenames[0].replace('.avi', '_CAT.tif')
        out_path_log = filenames[0].replace('.avi', '_CAT.csv')
    # run through the remaining files
    for i in range(1, len(filenames)):
        # load the next file
        im_n = load_avi(filenames[i])

        # concatenate it to the previous one
        im_1 = np.concatenate((im_1, im_n))
        # save the file name and the number of frames
        frames_list.append([filenames[i], im_n.shape[0]])
    # scale the output to max and turn into uint8 (for MiniAn)
    max_value = np.max(im_1)
    for idx, frames in enumerate(im_1):
        im_1[idx, :, :] = ((frames/max_value)*255).astype('uint8')
    # save the final stack
    io.imsave(out_path_tif, im_1, plugin='tifffile', bigtiff=True)
    # save the info about the files
    # frames_list = pd.DataFrame(frames_list, columns=['filename', 'frame_number'])
    # frames_list.to_csv(out_path_log)

    return out_path_tif, out_path_log, im_1


def extract_timestamp(frame):
    """Extract the timestamp from a wirefree miniscope frame, based on their example code"""

    footer = frame[-1, -8:]
    timestamp = footer[0] + (footer[1] << 8) + (footer[2] << 16) + (footer[3] << 24)
    return timestamp


def correct_timestamp_jumps(timestamps, jump_size=5):
    """Correct the jumps in the miniscope timestamps by interpolating the values around the jumps"""
    timestamps_corrected = timestamps.copy()

    # Find the jumps in the timestamps
    jump_idxs = np.argwhere(np.abs(np.diff(timestamps)) > jump_size)

    if jump_idxs.size == 0:
        jump_idxs = []
        jump_vals = []

    else:
        if jump_idxs.size == 1:
            jump_idxs = jump_idxs[0]
            jump_vals = np.diff(timestamps)[jump_idxs]
            jump_idxs += 1     # Add one for correct index
            timestamps_corrected[jump_idxs[0]:] = timestamps[jump_idxs[0]:] - jump_vals[0]

        else:
            jump_idxs = jump_idxs.squeeze()
            jump_vals = np.diff(timestamps)[jump_idxs]
            jump_idxs += 1     # Add one for correct index

            # If an odd number of discontinuities, handle the last one first
            if len(jump_idxs) % 2 != 0:

                timestamps_corrected[jump_idxs[-1]:] = timestamps[jump_idxs[-1]:] - jump_vals[-1]

                # Remove the last jump_idx and jump_val to make the arrays even
                jump_idxs_even = jump_idxs[:-1]
                jump_vals_even = jump_vals[:-1]
                    
                # Reshape the arrays to be pairs of jump_idxs and jump_vals
                jump_idxs_even = jump_idxs_even.reshape(-1, 2)
                jump_vals_even = jump_vals_even.reshape(-1, 2)

            else:
                # Reshape the arrays to be pairs of jump_idxs and jump_vals
                jump_idxs_even = jump_idxs.reshape(-1, 2)
                jump_vals_even = jump_vals.reshape(-1, 2)

            for jump_idx, jump_val in zip(jump_idxs_even, jump_vals_even):
                timestamps_corrected[jump_idx[0]:jump_idx[1]] = timestamps[jump_idx[0]:jump_idx[1]] - jump_val[0]

    # At this stage there are still little mistakes throughout that cause timing errors down the line.
    # Let's try to fix them by fitting a line to the timestamps and then using that as the correction
    x = np.arange(len(timestamps_corrected))
    slope, intercept = np.polyfit(x, timestamps_corrected, deg=1)
    regressed_timestamps = x * slope + intercept
    
    return regressed_timestamps, timestamps_corrected, jump_idxs, jump_vals


def insert_timestamps(timestamps_in, target_sync_in, miniscope_channel=4):
    """Insert the tif timestamps into the sync file corresponding to the target trial"""
    # read the file
    sync_info = pd.read_csv(target_sync_in, header=None)
    # find where the miniscope recordings start
    sync_start = np.argwhere(sync_info.iloc[:, miniscope_channel].to_numpy() > 3)
    # check that there is a trigger and that it's not a normal file (i.e. many triggers to probs doric)
    if sync_start.shape[0] == 0:
        return f'File {target_sync_in} does not have triggers'
    elif sync_start.shape[0] > 3:
        return f'File {target_sync_in} has too many triggers'
    else:
        sync_start = sync_start[0][0]
    # get the time vector from the trial
    trial_time = sync_info.iloc[:, 0].to_numpy()
    # add the offset to the timestamps
    timestamps_in += trial_time[sync_start]
    # find the closest sync index for each timestamp
    best_idx = np.searchsorted(trial_time, timestamps_in)
    # get rid of the frames occurring after the end of the experiment
    best_idx = best_idx[best_idx < sync_info.shape[0]]
    # modify the sync info to add the timestamps
    sync_info.iloc[best_idx, miniscope_channel] = 5
    # save the file (dropping index and header to match the original
    sync_info.to_csv(target_sync_in, index=False, header=False)
    return 'Successful insertion'


def process_latest_recording(wirefree_path, network_path, wirefree_processing_path=None):
    """Find the latest wirefree miniscope recording, concatenate the video into a tif, extract the timestamps,
    move the video file to a target network location with the corresponding name and overwrite the sync file"""

    # empty the processing folder
    if wirefree_processing_path is not None:
        delete_contents(wirefree_processing_path)
    
    # get the folders in the wirefree path
    folder_list = os.listdir(wirefree_path)
    folder_datetime = [datetime.datetime.strptime(el, '%m_%d_%Y') for el in folder_list]
    
    # get the current date and time
    current_datetime = datetime.datetime.now()
    
    # find the most recent one in day
    # TODO: make sure the subtraction is in the right direction and check whether thresholds are needed
    min_day = np.argmin([current_datetime - el for el in folder_datetime])
    target_path = os.path.join(wirefree_path, folder_list[min_day])
    
    # get the folders inside that day
    subfolder_list = os.listdir(target_path)
    subfolder_datetime = [datetime.datetime.strptime(el+'_'+folder_list[min_day], 'H%H_M%M_S%S_%m_%d_%Y')
                          for el in subfolder_list]
    
    # determine the most recent one in time
    min_time = np.argmin([current_datetime - el for el in subfolder_datetime])
    target_path = os.path.join(target_path, subfolder_list[min_time])
    
    # get the files in the folder
    video_list = os.listdir(target_path)
    
    # sort the names numerically (since they are numbered without 0 padding)
    video_numbers = np.argsort([int(el[5:-4]) for el in video_list])
    video_list = [os.path.join(target_path, video_list[el]) for el in video_numbers]

    # concatenate the video files in order and save as tiff
    old_tif, _, stack = concatenate_wirefree_video(video_list, wirefree_processing_path)
    
    # extract the timestamps (and convert to seconds)
    timestamps = np.array([extract_timestamp(el)/1000 for el in stack])

    # Correct the timestamps (known jumps in the miniscope firmware)
    regressed_timestamps, corrected_timestamps, _, _ = correct_timestamp_jumps(timestamps)

    # find the closest matching date in the network drive
    network_list_all = os.listdir(network_path)
    network_list = [el for el in network_list_all if '.txt' in el]
    network_datetime = [datetime.datetime.strptime(el[:19], '%m_%d_%Y_%H_%M_%S') for el in network_list]
    network_idx = np.argmin([current_datetime - el for el in network_datetime])
    
    # select the path
    target_network = network_list[network_idx]
    
    # create the path for the tif file
    new_tif = os.path.join(network_path, target_network.replace('.txt', '.tif'))
    
    # rename and transfer the tif file
    # only copy if the file doesn't exist, otherwise print a warning
    if not os.path.isfile(new_tif):
        # copy the file to the new folder with the new name
        shutil.copyfile(old_tif, new_tif)
    else:
        print(f'File {new_tif} already in network location')

    # find the matching sync file
    target_sync = [el for el in network_list_all if ('sync' in el) & (target_network[:19] in el)]
    target_sync_path = os.path.join(network_path, target_sync[0])
    
    # transfer the frame times to the corresponding sync file
    sync_check = insert_timestamps(regressed_timestamps, target_sync_path)
    print(sync_check)

    # Plot the timestamps to check for timing correction
    plt.plot(timestamps, label='Original timestamps')
    plt.plot(corrected_timestamps, label='Corrected timestamps')
    plt.plot(regressed_timestamps, label='Regressed timestamps')
    plt.show()

    return


if __name__ == '__main__':
    # run the processing of the latest recording
    process_latest_recording(paths.wirefree_path, paths.network_path, paths.wirefree_processing_path)
