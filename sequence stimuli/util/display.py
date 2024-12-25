"""
File: display.py
Author: Chuncheng Zhang
Date: 2024-11-01
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Qt6 on screen display for sequence stimuli.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-11-01 ------------------------
# Requirements and constants
import pandas as pd
import os
import sys
import time
import contextlib

import numpy as np

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

from rich import print
from pathlib import Path
from threading import Thread, RLock

from . import logger, CONFIG, current_dir
from .mk_sequence_from_dataframe_nsd import mk_sequence_from_dataframe_nsd

# %% ---- 2024-11-01 ------------------------
# Function and class
app = QApplication(sys.argv)
logger.debug(f'App: {app}')

screen = app.screens()[CONFIG.display.screenId]
logger.debug(f'Screen: {CONFIG.display.screenId}: {screen}, {screen.size()}')


class OnScreenDisplay(object):
    app = app
    screen = screen

    window = QMainWindow()
    pixmap_container = QLabel(window)
    pixmap = None

    width = CONFIG.display.width
    height = CONFIG.display.height

    running = False

    _rlock = RLock()

    def __init__(self):
        self._prepare_window()
        logger.info(f'Initialized {self}')

    def _prepare_window(self):
        """
        Prepare the window for displaying images on screen.

        This function sets various attributes and configurations for the window,
        including translucency, framelessness, topmost position, size, and geometry.
        It also sets the pixmap container within the window bounds.

        Parameters:
        None

        Returns:
        None
        """
        # Translucent image by its RGBA A channel
        self.window.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Disable frame and keep the window on the top layer.
        # It is necessary to set the FramelessWindowHint for the WA_TranslucentBackground works.
        # The WindowTransparentForInput option disables interaction.
        self.window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.WindowTransparentForInput
        )

        # Set the window size
        self.window.resize(self.width, self.height)

        # Put the window to the NW corner
        rect = self.screen.geometry()
        self.window.move(rect.x(), rect.y())

        # Set the pixmap_container accordingly,
        # and it is within the window bounds
        self.pixmap_container.setGeometry(0, 0, self.width, self.height)

    @contextlib.contextmanager
    def acquire_lock(self):
        '''Lock the context'''
        self._rlock.acquire()
        try:
            yield
        finally:
            self._rlock.release()

    def repaint(self):
        """
        Update the display with the current pixmap.

        This function acquires a lock to ensure thread safety while updating the display.
        It checks if a pixmap is available and sets it to the pixmap container within the window.

        Parameters:
        None

        Returns:
        None
        """
        with self.acquire_lock():
            if pixmap := self.pixmap:
                self.pixmap_container.setPixmap(pixmap)
        return

    def main_loop(self):
        """
        Start a daemon thread to continuously generate images and update the display.
        This function creates a new daemon thread that runs the `_main_loop` method.

        Parameters:
        None

        Returns:
        None
        """
        Thread(target=self._main_loop, daemon=True).start()

    def get_running_state(self):
        return self.running

    def stop_running(self):
        self.running = False
        return

    def _main_loop(self):
        """
        The main loop for the on-screen display.

        This function continuously generates images based on the current time and updates the display.
        It measures the frame rate and prints it every 10 frames.

        Parameters:
        None

        Returns:
        None
        """
        report_interval = 2  # seconds
        next_report_time = report_interval  # seconds

        self.running = True
        tic = time.time()
        i = 0
        loop_id = f'Loop-{np.random.random():.4f}-{time.time():.8f}'
        logger.debug(f'Start running: {loop_id}')
        while self.running:
            i += 1
            t = time.time()-tic

            # Generate the frame img
            img = self.generate_img(t)
            # Put the img into pixmap
            if self.running:
                with self.acquire_lock():
                    self.pixmap = QPixmap.fromImage(ImageQt(img))

            # ! Sleep or not
            # time.sleep(0.01)

            # Report frame rate
            if t > next_report_time:
                print(f'Frame rate: {i/t:0.2f}')
                next_report_time += next_report_time

        logger.debug(f'Stopped running: {loop_id}')

    def place_img(self, img: Image):
        mat = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        mat[:, :, 3] = 255
        bg = Image.fromarray(mat, mode='RGBA')

        a1 = bg.width / bg.height
        a2 = img.width / img.height

        # Fit on the height
        if a1 > a2:
            img = img.resize((int(bg.height*a2), bg.height))
            bg.paste(img, (int((bg.width-img.width)/2), 0))
        # Fit on the width
        else:
            img = img.resize((bg.width, int(bg.width/a2)))
            bg.paste(img, (0, int((bg.height-img.height)/2)))
        logger.debug(f'Resized img: {img.size}')

        self.pixmap = QPixmap.fromImage(ImageQt(bg))


class SequenceStimuli(OnScreenDisplay):
    images_df: pd.DataFrame
    image_mode: str

    def __init__(self, images_df: pd.DataFrame, image_mode: str, debug=False):
        """
        Initialize the EccentricityMapping class, which inherits from OnScreenDisplay.

        This constructor calls the parent class's constructor (__init__ method) using the super() function.
        It does not take any parameters and does not return any value.
        """
        super().__init__()
        self.images_df = images_df
        self.image_mode = image_mode
        self.read_images()
        self.place_prompt_img()
        self.setup()
        self.change_focus_color()
        self.debug = debug

    def change_focus_color(self, t: float = 0) -> str:
        """
        Change the color of the focus point for the next trial.

        This function randomly selects a new color from the list of available colors,
        updates the next time point for color change, and logs the color change.

        It also ensures that the changed color is different from the current one.

        Parameters:
            t (float): The current time point in the sequence stimuli. Default is 0.

        Returns:
            str: The color of the focus point after the change.
        """
        d = np.random.uniform(CONFIG.focusPoint.tMin, CONFIG.focusPoint.tMax)
        self.t_next_change_focus_color = t+d

        c = CONFIG.focusPoint.colors.pop(0)
        np.random.shuffle(CONFIG.focusPoint.colors)
        CONFIG.focusPoint.colors.append(c)

        logger.debug(
            f'Changed focus point color from {c} to {CONFIG.focusPoint.colors[0]}')

        logger.debug(
            f'Next focus point color changing dues to {t} -> {self.t_next_change_focus_color}')

        return CONFIG.focusPoint.colors[0]

    def place_prompt_img(self):
        img = Image.open(
            current_dir.joinpath(CONFIG.prompt.img)).convert('RGBA')
        self.place_img(img)
        return

    def setup(self):
        '''
        Setup the time points for displaying the image.
        The on(+) and off(_) times of the image is as following:

        0 -> t1 --------> t2 -> trial_length
        ______/+++++++++++\______

        '''
        cis = CONFIG.imgSequence
        self.trial_length = cis.paddingBefore + cis.paddingAfter + cis.duration
        self.t1 = cis.paddingBefore
        self.t2 = cis.paddingBefore + cis.duration
        # Start the index of the image from the -1, it increases as the display goes
        self.idx = -1
        return

    def get_alpha(self, t):
        '''Return 0-255 alpha value for the given time t.'''
        beta = 50
        t %= self.trial_length

        # On left edge of duration
        if abs(t-self.t1) < abs(t-self.t2):
            t -= self.t1
            t *= beta
            a = np.exp(t) / (1+np.exp(t))
            return np.floor((a*255)).astype(np.uint8)
        # On right edge of duration
        else:
            t -= self.t2
            t *= beta
            a = (1-np.exp(t) / (1+np.exp(t)))
            return np.ceil(a*255).astype(np.uint8)

    def read_images(self):
        # Read the images
        paths = mk_sequence_from_dataframe_nsd(self.images_df, self.image_mode)
        imgs = [Image.open(p) for p in paths]
        names = ['{}-{}'.format(self.image_mode, p.name) for p in paths]

        # Resize the images
        size = (CONFIG.imgSize.width, CONFIG.imgSize.height)
        # size = (self.width, self.height)
        imgs = [e.resize((size)) for e in imgs]

        # Convert the images to 'RGBA'
        imgs = [e.convert('RGBA') for e in imgs]

        # Remember the images and names.
        self.imgs = imgs
        self.names = names

        # Compute the img_offsets.
        # It is the left-top coordinate of the image inside the screen.
        # It keeps the image always in the center of the screen.
        self.img_offsets = ((self.width-CONFIG.imgSize.width)//2,
                            (self.height-CONFIG.imgSize.height)//2)

        # Report
        logger.debug(f'Read images({len(imgs)})')
        logger.debug(f'The images are {names}')
        return

    def generate_img(self, t: float) -> Image.Image:
        '''Implementation of the generate_img method'''

        # Check the experiment progress.
        idx = int(t // self.trial_length)

        def get_and_prepare_img(idx, t):
            # Get the image and its name.
            # img = self.imgs[idx % len(self.imgs)].copy()
            name = self.names[idx % len(self.names)]

            # Trigger it out when the image displays on the screen.
            if idx > self.idx:
                self.idx = idx
                logger.debug(f'Display img: {idx} | {name}')

            # Get and set the img's alpha channel.
            alpha = self.get_alpha(t)
            r = alpha / 255

            # Now it only works with pure black background.
            mat = np.array(img).astype(np.float32)
            mat *= r
            img = Image.fromarray(mat.astype(np.uint8), mode='RGBA')
            img.putalpha(255)

            # Paste the image into the center.
            # The color is initialized from the imgSequence.background (r, g, b, a).
            mat = np.zeros((self.height, self.width, 4))
            mat[:, :] = CONFIG.imgSequence.background
            img_backer = Image.fromarray(mat.astype(np.uint8), mode='RGBA')
            img_backer.paste(img, self.img_offsets)

            return img_backer, name

        def mk_bg_img():
            # Generate the image and its drawing context.
            # The initializing color is (0, 0, 0, 0) for all the pixels
            mat = np.zeros((self.height, self.width, 4))
            mat[:, :] = CONFIG.imgSequence.background
            bg_img = Image.fromarray(mat.astype(np.uint8), mode='RGBA')
            return bg_img

        # Get the img and its background img
        img, name = get_and_prepare_img(idx, t)
        bg_img = mk_bg_img()

        # Put the img on the top of bg_img,
        # by compositing img and bg_img, the mask is img.
        # So, the mask is used for alpha transparency.
        img = Image.composite(img, bg_img, mask=img)
        draw = ImageDraw.Draw(img)

        # Debug display
        if self.debug:
            # Display the progress bar
            tt = t % self.trial_length
            r1 = tt / self.trial_length

            draw.rectangle(
                (0, 0, self.width*r1, 10), outline=CONFIG.colors.debugColor)

            if tt > self.t1:
                r21 = self.t1 / self.trial_length
                r22 = min(tt, self.t2) / self.trial_length
                draw.rectangle(
                    (self.width*r21, 0, self.width*r22, 10), fill=CONFIG.colors.debugColor)

        # Put the focus point on the center
        if CONFIG.focusPoint.toggled:
            if t > self.t_next_change_focus_color:
                self.change_focus_color(t)

            radius = CONFIG.focusPoint.radius
            color = CONFIG.focusPoint.colors[0]
            box = (
                self.width//2-radius, self.height//2-radius, self.width//2+radius, self.height//2+radius)
            draw.ellipse(box, fill=color)

        return img


# %% ---- 2024-11-01 ------------------------
# Play ground


# %% ---- 2024-11-01 ------------------------
# Pending


# %% ---- 2024-11-01 ------------------------
# Pending
