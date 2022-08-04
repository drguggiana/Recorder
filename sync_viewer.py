from functions_nidaq import load_csv, plot_inputs_vr, plot_inputs_miniscope
from tkinter import filedialog
from paths import sync_path
from tkinter import Tk


def get_tk_file(initial_path):
    root = Tk()
    root.withdraw()
    return filedialog.askopenfilenames(initialdir=initial_path, filetypes=(("csv files", "*.csv"),))[0]


# select the sync file to visualize
file_path = get_tk_file(sync_path)

# load the data in the file
sync_data = load_csv(file_path)

# determine whether it's a miniscope or VR file and plot accordingly
plot_inputs_vr(sync_data)


# root.destroy()
