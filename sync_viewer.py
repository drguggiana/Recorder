from functions_recorder import load_csv, plot_inputs_vr, plot_inputs_miniscope
import tkFileDialog
from paths import sync_path
from Tkinter import Tk


def get_tk_file(initial_path):
    root = Tk()
    root.withdraw()
    return tkFileDialog.askopenfilenames(initialdir=initial_path, filetypes=(("csv files", "*.csv"),))[0]


# select the sync file to visualize
file_path = get_tk_file(sync_path)

# load the data in the file
sync_data = load_csv(file_path)

# determine whether it's a miniscope or VR file and plot accordingly
if 'syncVR' in file_path:
    plot_inputs_vr(sync_data)
else:
    plot_inputs_miniscope(sync_data)

# root.destroy()
