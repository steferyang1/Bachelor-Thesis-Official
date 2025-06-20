#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: Jordy Thielen (jordy.thielen@donders.ru.nl)

Python implementation of a keyboard for the noise-tagging project.
"""

import json
import numpy as np
from psychopy import visual, event, monitors, misc
from psychopy import core
import random
import itertools
import pyntbci

FR = 60
PR = 60  # codes presentation rate

class Keyboard(object):
    """
    A keyboard with keys and text fields.
    """

    def __init__(self, size, width, distance, screen=0, window_color=(0, 0, 0), stream=True, stream_postfix=""):
        """
        Create a keyboard.

        Args:
            size (array-like): 
                The (width, height) of the window in pixels, i.e., resolution
            width (float):
                The width of the screen in centimeters
            distance (float):
                The distance of the user to the screen in centimeters
            screen (int):
                The screen number that is used, default: 0
            window_color (array-like):
                The background color of the window, default: (0, 0, 0)
            stream (bool):
                Whether or not to log events/markers in an LSL stream. Default: True
        """
        # Set up monitor (sets pixels per degree)
        self.monitor = monitors.Monitor("testMonitor", width=width, distance=distance)
        self.monitor.setSizePix(size)

        # Set up window
        self.window = visual.Window(monitor=self.monitor, screen=screen, units="pix", size=size, color=window_color, fullscr=False, waitBlanking=False, allowGUI=False)
        self.window.setMouseVisible(False)

        # Initialize keys and fields
        self.keys = dict()
        self.fields = dict()

        # Setup LSL stream
        self.stream = stream
        if self.stream:
            from pylsl import StreamInfo, StreamOutlet
            self.outlet = StreamOutlet(StreamInfo(name='KeyboardMarkerStream'+stream_postfix, type='Markers', channel_count=1, nominal_srate=0, channel_format='string', source_id='KeyboardMarkerStream'+stream_postfix))

    def get_size(self):
        """
        Get the size of the window in pixels, i.e., resolution.

        Returns:
            (array-like): 
                The (width, height) of the window in pixels, i.e., resolution
        """
        return self.window.size

    def get_pixels_per_degree(self):
        """
        Get the pixels per degree of visual angle of the window.

        Returns:
            (float): 
                The pixels per degree of visual angle
        """
        return misc.deg2pix(1.0, self.monitor)

    def get_framerate(self):
        """
        Get the framerate in Hz of the window.

        Returns:
            (float): 
                The framerate in Hz
        """
        #infoMsg="" --> this makes sure that the annoying message in the middle is removed
        return int(np.round(self.window.getActualFrameRate(infoMsg="")))

    def add_key(self, name, size, pos, images=["black.png", "white.png"]):
        """
        Add a key to the keyboard.

        Args:
            name (str):
                The name of the key, if none then text is used
            size (array-like):
                The (width, height) of the key in pixels
            pos (array-like):
                The (x, y) coordinate of the center of the key, relative to the center of the window
            images (array-like):
                The images of the key. The first image is the default key. Indices will correspond to the 
                values of the codes. Default: ["black.png", "white.png"]
        """
        assert name not in self.keys, "Trying to add a box with a name that already extists!"
        self.keys[name] = []
        for image in images:
            self.keys[name].append(visual.ImageStim(win=self.window, image=image, 
            units="pix", pos=pos, size=size, autoLog=False))

        # Set autoDraw to True for first default key to keep app visible
        self.keys[name][0].setAutoDraw(True)

    def add_text_field(self, name, text, size, pos, field_color=(0, 0, 0), text_color=(-1, -1, -1)):
        """
        Add a text field to the keyboard.

        Args:
            name (str):
                The name of the text field, if none then text is used
            text (str):
                The text on the text field
            size (array-like):
                The (width, height) of the text field in pixels
            pos (array-like):
                The (x, y) coordinate of the center of the text field, relative to the center of the window
            field_color (array-like):
                The color of the background of the text field, default: (0, 0, 0)
            text_color (array-like):
                The color of the text on the text field, default: (-1, -1, -1)
        """
        assert name not in self.fields, "Trying to add a text field with a name that already extists!"
        self.fields[name] = self.fields[name] = visual.TextBox2(win=self.window, text=text, font='Courier', 
            units="pix", pos=pos, size=size, letterHeight=0.5*size[1], 
            color=text_color, fillColor=field_color, alignment="left", 
            autoDraw=True, autoLog=False)

    def set_field_text(self, name, text):
        """
        Set the text of a text field.

        Args:
            name (str):
                The name of the key
            text (str):
                The text
        """
        self.fields[name].setText(text)
        self.window.flip()

    def log(self, marker, on_flip=False):
        if self.stream and not marker is None:
            if not isinstance(marker, list):
                marker = [marker]
            if on_flip:
                self.window.callOnFlip(self.outlet.push_sample, marker)
            else:
                self.outlet.push_sample(marker)    
    
    def run(self, codes, duration=None, start_marker=None, stop_marker=None):
        """
        Present a trial with concurrent flashing of each of the symbols.

        Args:
            codes (dict): 
                A dictionary with keys being the symbols to flash and the value a list (the code 
                sequence) of integer states (images) for each frame
            duration (float):
                The duration of the trial in seconds. If the duration is longer than the code
                sequence, it is repeated. If no duration is given, the full length of the first 
                code is used. Default: None
        """
        # Set number of frames
        if duration is None:
            n_frames = len(codes[list(codes.keys())[0]])
        else:
            n_frames = int(duration * FR)

        # Set autoDraw to False for full control
        for key in self.keys.values():
            key[0].setAutoDraw(False)

        # Send start marker
        self.log(start_marker, on_flip=True)

        # Loop frame flips
        for i in range(n_frames):

            # Check quiting
            if i % 60 == 0:
                if self.is_quit():
                    self.quit()

            # Draw keys with color depending on code state
            for name, code in codes.items():
                # added int()
                self.keys[name][int(code[i % len(code)])].draw()
            self.window.flip()

        # Send stop markers
        self.log(stop_marker)

        # Set autoDraw to True to keep app visible
        for key in self.keys.values():
            key[0].setAutoDraw(True)
        self.window.flip()

    def is_quit(self):
        """
        Test if a quit is forced by the user by a key-press.

        Returns:
            (bool): 
                True is quit forced, otherwise False
        """
        # If quit keys pressed, return True
        if len(event.getKeys(keyList=["q", "escape"])) > 0:
            return True
        return False

    def quit(self):
        """
        Quit the keyboard.
        """
        self.window.setMouseVisible(True)
        self.window.close()
        core.quit()


def run_condition(classes=None, images=None, stream_postfix=""):
    """
    Example experiment with initial setup and highlighting and presenting a few trials.
    """

    STREAM = True
    SCREEN = 1
    SCREEN_SIZE = (2560, 1440)  # Mac: (1792, 1120), LabPC: (1920, 1080), Steven: (1920/1.25, 1080/1.25)
    SCREEN_WIDTH = 53.0  # Mac: (34,5), LabPC: 53.0
    SCREEN_DISTANCE = 50.0
    SCREEN_COLOR = (0, 0, 0)

    N_TRIALS = 30
    trial_list = np.random.permutation(np.arange(classes).repeat(int(np.ceil(N_TRIALS / classes))))[:N_TRIALS]
    STT_WIDTH = 2.2
    STT_HEIGHT = 2.2

    TEXT_FIELD_HEIGHT = 5.0

    KEY_WIDTH = 3.75
    KEY_HEIGHT = 3.75
    KEY_SPACE = 1.0

    if images == "bw":
        KEY_COLORS = ["black", "white", "green"]
    elif images == "grating":
        KEY_COLORS = ["gray", "grating", "green"]
    else:
        raise Exception("Unknown images:", images)
    
    if classes == 5:
        #use 12 shift m_sequence
        codes = pyntbci.stimulus.shift(pyntbci.stimulus.make_m_sequence(), 12)
        KEYS = [
        ["W"], 
        ["A", "S", "D"], 
        ["X"]]
    elif classes == 30:
        #use 2 shift m_sequence
        codes = pyntbci.stimulus.shift(pyntbci.stimulus.make_m_sequence(), 2)
        KEYS = [
            ["A", "B", "C", "D", "E", "F"],
            ["G", "H", "I", "J", "K", "L"],
            ["M", "N", "O", "P", "Q", "R"],
            ["S", "T", "U", "V", "W", "X"], 
            ["Y", "Z", "_", ".", "question", "!"]]
    else:
        raise Exception("Unkonwn classes:", classes)
    KEYS_ordered = [x for k in KEYS for x in k]

    CUE_TIME = 0.8
    TRIAL_TIME = 4.2

    # Initialize keyboard
    keyboard = Keyboard(size=SCREEN_SIZE, width=SCREEN_WIDTH, distance=SCREEN_DISTANCE, screen=SCREEN, window_color=SCREEN_COLOR, stream=STREAM, stream_postfix=stream_postfix)
    ppd = keyboard.get_pixels_per_degree()

    # Add stimulus timing tracker at left top of the screen
    x_pos = -SCREEN_SIZE[0] / 2 + STT_WIDTH / 2 * ppd 
    y_pos = SCREEN_SIZE[1] / 2 - STT_HEIGHT / 2 * ppd 
    images = ["images/black.png", "images/white.png"]
    keyboard.add_key("stt", (STT_WIDTH * ppd, STT_HEIGHT * ppd), (x_pos, y_pos), images)

    # Add text field at the top of the screen
    x_pos = STT_WIDTH * ppd
    y_pos = SCREEN_SIZE[1] / 2 - TEXT_FIELD_HEIGHT * ppd / 2
    keyboard.add_text_field("text", "", (SCREEN_SIZE[0] - STT_WIDTH * ppd, TEXT_FIELD_HEIGHT * ppd), (x_pos, y_pos), (0, 0, 0), (-1, -1, -1))

    # Add the keys
    for y in range(len(KEYS)):
        for x in range(len(KEYS[y])):
            x_pos = (x - len(KEYS[y]) / 2 + 0.5) * (KEY_WIDTH + KEY_SPACE) * ppd
            y_pos = -(y - len(KEYS) / 2) * (KEY_HEIGHT + KEY_SPACE) * ppd - TEXT_FIELD_HEIGHT * ppd
            images = [f"images/{KEYS[y][x]}_{color}.png" for color in KEY_COLORS]
            keyboard.add_key(KEYS[y][x], (KEY_WIDTH * ppd, KEY_HEIGHT * ppd), (x_pos, y_pos), images)

    # Load sequences!
    tmp = codes
    codes = dict()
    i = 0
    for row in KEYS:
        for key in row:
            codes[key] = np.repeat(tmp[i, :], int(FR / PR)).tolist()
            i += 1
    codes["stt"] = [1, 1] + [0] * int((1 + TRIAL_TIME) * keyboard.get_framerate())


    # Set highlights
    highlights = dict()
    for row in KEYS:
        for key in row:
            highlights[key] = [0]
    highlights["stt"] = [0]

    # Wait for start
    keyboard.set_field_text("text", "Press button to start.")
    print("Press button to start.")
    event.waitKeys()
    keyboard.set_field_text("text", "")
    print("Starting.")

    keyboard.log([f"condition;classes={classes};images={images}"])
    keyboard.log([f"codes;{json.dumps(codes)}"])

    # Start run
    keyboard.log(marker=["start_run"])
    keyboard.set_field_text("text", "Starting...")
    keyboard.run(highlights, 5.0)
    keyboard.set_field_text("text", "")

    # Loop trials
    for i_trial in range(N_TRIALS):

        # Set target
        target = trial_list[i_trial]
        target_key = KEYS_ordered[target]
        print(f"{1 + i_trial:03d}/{N_TRIALS}\t{target_key}\t{target}")
        
        # Cue
        highlights[target_key] = [2]
        keyboard.run(highlights, CUE_TIME, 
            start_marker=[f"start_cue;trial={i_trial};target={target};key={target_key}"], 
            stop_marker=[f"stop_cue;trial={i_trial}"])
        highlights[target_key] = [0]

        # Trial
        keyboard.run(codes, TRIAL_TIME, 
            start_marker=[f"start_trial;trial={i_trial}"], 
            stop_marker=[f"stop_trial;trial={i_trial}"])

    # Wait for stop
    keyboard.set_field_text("text", "Stopping...")
    keyboard.log(marker=["stop_run"])
    keyboard.run(highlights, 5.0)
    keyboard.set_field_text("text", "Press button to continue.")
    print("Press button to continue.")
    event.waitKeys(keyList="c")
    keyboard.set_field_text("text", "")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test keyboard.py")
    parser.add_argument("-n", "--ntrials", type=int, help="number of trials", default=5)
    parser.add_argument("-c", "--code", type=str, help="code set to use", default="mseq_61_shift_2")
    args = parser.parse_args()

    # All the 4 conditon function in an array
    latin_square = [[1, 2, 4, 3, 2, 3, 1, 4],  # row
                    [2, 3, 1, 4, 1, 2, 4, 3],  # row, rotated by 1 to the left   
                    [3, 4, 2, 1, 4, 1, 3, 2],  # row, rotated by 2 to the left
                    [4, 1, 3, 2, 3, 4, 2, 1],  # row, rotated by 3 to the left
                    [1, 2, 4, 3, 1, 2, 4, 3],
                    [2, 3, 1, 4, 2, 3, 1, 4],
                   ]
    
    participant_nr = 0 #from 0 to 5

    for i, i_condition in enumerate(latin_square[participant_nr]):
        #bw 30
        if i_condition == 1:
            run_condition(classes = 30, images = "bw", stream_postfix=str(1+i))
        #grating 5
        elif i_condition == 2:
            run_condition(classes = 5, images = "grating", stream_postfix=str(1+i))
        #bw 5
        elif i_condition == 3:
            run_condition(classes = 5, images = "bw", stream_postfix=str(1+i))
        #grating 30
        elif i_condition == 4:
            run_condition(classes = 30, images = "grating", stream_postfix=str(1+i))







#run_condition(code = "mseq_61_shift_2", classes = 30, images = "grating")
    #preprocessing:
    # 0. import raw data
    # 0.5 Channel selection % re-referencing
    # 1. revmoing bad channels
    # 2. spectral filtering
    # 3. epoching
    # 4. resampling of data/ down sampling (needs a spectral filter too) (doing this before epoching, your marker time points will shift. So we STILL downsample after epoching)
    
    #latin square randomization!!!!!!!!!!!!!!!!!!!!
    #check presentation rate
    #check gabor patch similar to the paper.
    #distance from screen === 50cm
    #size of the patch === 10px by 20px
    #how many gabor patches === 75 patches per button radnomized on the screen using a uniform distribution
    #size of buttons === 150px diameter