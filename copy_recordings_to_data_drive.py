import os
import shutil


def copy_to_target(source_directory, target_directory, target_conflict_directory=None, excluded=['suffix', 'test']):
    files_on_source = os.listdir(source_directory)
    files_on_target = os.listdir(target_directory)

    if target_conflict_directory is not None:
        conflict_files = os.listdir(target_conflict_directory)
        files_on_target += conflict_files

    # Check for files on source drive that are not on target
    not_on_target = [file for file in files_on_source if file not in files_on_target]

    # Exclude files containing these words
    not_on_target = [file for file in not_on_target if not any(word in file for word in excluded)]

    print(f"Copying {len(not_on_target)} files to {target_directory}...")

    for file_name in not_on_target:
        full_file_name = os.path.join(source_directory, file_name)
        if os.path.isfile(full_file_name):
            print(f"    ... {full_file_name}")
            shutil.copy2(full_file_name, target_directory)

    print(f"All files transferred to {target_directory}!\n")


data_directory = r'C:\Users\setup\Documents\VR_files'
backup_directory = r'F:\vr_data_backup'
server_directory = r'Z:\Prey_capture\VRExperiment'
conflict_directory = r'Z:\Prey_capture\conflict_files\VTuningWF'
archive_directory = r'I:\Matthew McCann\vr_rig\VTuningWF'

# Copy files to local backup
copy_to_target(data_directory, backup_directory)

# Copy files to server
copy_to_target(data_directory, server_directory, target_conflict_directory=conflict_directory)

# Copy files to archive
copy_to_target(data_directory, archive_directory)

print('Done!')


