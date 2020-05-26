from tkSimpleDialog import askstring
import Tkinter as tk
import os
import numpy as np


def get_filename_suffix():
    """Use a mini GUI to get a string from the user"""
    root = tk.Tk()
    root.withdraw()
    return askstring('Input animal name', 'Please input animal name')


def replace_name_part(paths, replace_this, with_this):
    """Replace the replace_this string with the with_this string in the file names from the paths list provided"""
    # initialize a counter for the files
    file_counter = 0
    # initialize a list to store the failed paths
    failed_paths = []
    # initialize a list for replaced names to output
    new_names = []
    # for all the paths
    for file_path in paths:
        # check if the old path exists
        if not os.path.isfile(file_path):
            failed_paths.append('_'.join(('old', file_path)))
            continue
        # create the new path
        new_path = file_path.replace(replace_this, with_this)
        # check if the new path exists
        if os.path.isfile(new_path):
            failed_paths.append('_'.join(('new', new_path)))
            continue
        # change the file_name
        print(file_path)
        print(new_path)
        os.rename(file_path, new_path)
        # add it to the list of renamed paths
        new_names.append(new_path)
        # update the counter
        file_counter += 1
    print("_".join(("Total original files: ", str(len(paths)), "Successfully renamed files: ", str(file_counter))))
    return failed_paths, new_names


def replace_name_approx(target_directory, name_source, new_name, threshold=100, extension=None):
    """Find the file in the target_directory (matching the desired extension if provided) that most closely matches
    the creation time of the name_source (up to a tolerance of threshold) and rename it based on the new_name"""
    # get the files in the folder
    file_list = [os.path.join(target_directory, el) for el in os.listdir(target_directory)]
    if extension is not None:
        file_list = [el for el in file_list if el.endswith(extension)]
    # sort them by creation date
    creation_times = [os.path.getmtime(os.path.join(target_directory, el)) for el in file_list]
    creation_indexes = np.argsort(-np.array(creation_times))
    # get the creation date of the target file
    target_time = os.path.getmtime(name_source)
    # run through the files from the newest
    for index in creation_indexes:

        # if it matches the creation date threshold, rename and return True
        if np.abs(target_time - creation_times[index]) < threshold:
            os.rename(file_list[index], new_name)
            return True
    # if not, print there was no file found and return False
    print('No matching file was found')
    return False

#     root = tk.Tk()
#     button = tk.Button(root, text='Enter string', command=get_string)
#     button.pack()
#     root.mainloop()
#     return button.get
#
#
# def get_string():
#     ans = askstring('Input animal name', 'Please input animal name')
#     return ans
