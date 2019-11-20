from tkSimpleDialog import askstring
import Tkinter as tk
import os


def get_filename_suffix():
    root = tk.Tk()
    root.withdraw()
    return askstring('Input animal name', 'Please input animal name')


def replace_name_part(paths, replace_this, with_this):
    """Replace the replace_this string with the with_this string in the file names from the paths list provided"""
    # initialize a counter for the files
    file_counter = 0
    # initialize a list to store the failed paths
    failed_paths = []
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
        os.rename(file_path, new_path)
        # update the counter
        file_counter += 1
    print("_".join(("Total original files: ", str(len(paths)), "Successfully renamed files: ", str(file_counter))))
    return failed_paths

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
