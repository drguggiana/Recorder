import time
from numpy import sqrt


class VRScreenTrialStructure:
    """A class to handle the trial structure of the VR Screen experiment"""

    def __init__(self, trials, isi):
        # These variables are all attributes of the trial structure class so they can be modified by calls to
        # functions from different threads
        self.df = trials
        self.isi = isi

        self.in_session = True
        self.start_trial = False
        self.in_trial = False

        self.num_trials = len(self.df)
        self.trial_idx = 0

        self.trial_start_time = 0
        self.trial_end_time = 0

        self.long_wall = 1.0    # meters
        self.short_wall = 0.5    # meters
        self.duration = self.calculate_duration()

    def handshake(self, *values):
        """Function for debugging osc communication"""
        print("Trial {} received".format(values[0]))

    def end_trial(self, *values):
        """Receives message for trial end and increments to next trial"""
        self.in_trial = False
        self.trial_end_time = time.time()
        print("Trial {} completed\n".format(values[0]))

        if self.trial_idx < self.num_trials - 1:
            self.trial_idx += 1
        else:
            self.in_session = False

    def assemble_trial_message(self):
        """Assemble the OSC message to get sent to Unity"""
        row = self.df.iloc[self.trial_idx].to_list()
        trial_message = [int(self.trial_idx + 1)] + row
        trial_message = [str(tm) for tm in trial_message]
        return trial_message

    def check_ISI(self):
        """Check time since last trial end to determine if the next trial starts"""
        now = time.time()
        if now - self.trial_end_time >= self.isi:
            self.start_trial = True

    def calculate_duration(self):
        total_isi = self.isi * (self.num_trials - 1)
        speeds = self.df['speed'].to_list()
        trajectories = self.df['trajectory'].to_list()
        distances = [sqrt(self.long_wall**2 + self.short_wall**2) if t >= 2 else self.long_wall for t in trajectories]
        trial_times = [d / s for d, s in zip(distances, speeds)]
        duration = total_isi + sum(trial_times)
        return duration


class VRTuningTrialStructure:
    """A class to handle the trial structure of the VR Tuning experiment"""

    def __init__(self, trials, trial_duration=2, isi=1):
        # These variables are all attributes of the trial structure class so they can be modified by calls to
        # functions from different threads
        self.df = trials
        self.isi = isi    # seconds
        self.trial_duration = trial_duration     # sec

        self.in_session = True
        self.start_trial = True

        self.num_trials = len(self.df)
        self.trial_idx = 0
        self.duration = self.calculate_duration()

    def handshake(self, *values):
        """Function for debugging osc communication"""
        print("Trial {} received".format(values[0]))

    def end_trial(self, *values):
        """Receives message for trial end and increments to next trial"""
        print("Trial {} completed\n".format(values[0]))

        if self.trial_idx < self.num_trials - 1:
            self.trial_idx += 1
            self.start_trial = True
        else:
            self.in_session = False

    def assemble_setup_message(self):
        setup_message = [str(self.trial_duration), str(self.isi)]
        return setup_message

    def assemble_trial_message(self):
        """Assemble the OSC message to get sent to Unity"""
        row = self.df.iloc[self.trial_idx].to_list()
        trial_message = [int(self.trial_idx + 1)] + row
        trial_message = [str(tm) for tm in trial_message]
        return trial_message

    def calculate_duration(self):
        total_isi = self.isi * (self.num_trials - 1)
        total_trial_time = self.trial_duration * (self.num_trials - 1)
        duration = total_isi + total_trial_time
        return duration
