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

from . import logger, config, current_dir

# %% ---- 2024-11-01 ------------------------
# Function and class
app = QApplication(sys.argv)
logger.debug(f'App: {app}')

screen = app.screens()[config.display.screenId]
logger.debug(f'Screen: {config.display.screenId}: {screen}, {screen.size()}')


class OnScreenDisplay(object):
    app = app
    screen = screen

    window = QMainWindow()
    pixmap_container = QLabel(window)
    pixmap = None

    width = config.display.width
    height = config.display.height

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
    def __init__(self, debug=False):
        """
        Initialize the EccentricityMapping class, which inherits from OnScreenDisplay.

        This constructor calls the parent class's constructor (__init__ method) using the super() function.
        It does not take any parameters and does not return any value.
        """
        super().__init__()
        self.read_images()
        self.place_prompt_img()
        self.setup()
        self.debug = debug

    def place_prompt_img(self):
        img = Image.open(
            current_dir.joinpath(config.prompt.img)).convert('RGBA')
        self.place_img(img)
        return

    def setup(self):
        cis = config.imgSequence
        self.trial_length = cis.paddingBefore + cis.paddingAfter + cis.duration
        self.t1 = cis.paddingBefore
        self.t2 = cis.paddingBefore + cis.duration
        # Start from the -1, it increases as the display goes
        self.idx = -1
        return

    def get_alpha(self, t):
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
        # Read the images from directory
        directory = Path(config.imgSequence.directory.replace(
            '<home>', os.environ.get('USERPROFILE')))
        files = [
            p for p in directory.iterdir()
            if any(p.name.endswith(e) for e in config.extensions)]
        imgs = [Image.open(p) for p in files]
        names = [p.name for p in files]

        # Resize the images
        size = (config.imgSize.width, config.imgSize.height)
        size = (self.width, self.height)
        imgs = [e.resize((size)) for e in imgs]

        # Convert the images to 'RGBA'
        imgs = [e.convert('RGBA') for e in imgs]

        # Record
        self.imgs = imgs
        self.names = names

        # Report
        logger.debug(f'Read images({len(imgs)}) from {directory}')
        logger.debug(f'The images are {names}')
        return

    def generate_img(self, t: float) -> Image.Image:
        idx = int(t // self.trial_length)

        # Generate the image and its drawing context.
        # The initializing color is (0, 0, 0, 0) for all the pixels
        mat = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        bg_img = Image.fromarray(mat.astype(np.uint8)+100, mode='RGBA')

        img = self.imgs[idx % len(self.imgs)].copy()
        name = self.names[idx % len(self.names)]

        if idx > self.idx:
            self.idx = idx
            logger.debug(f'Display img: {idx} | {name}')

        alpha = self.get_alpha(t)
        img.putalpha(alpha)

        # Put the img on the top of bg_img.
        # the mask is used for alpha transparency
        img = Image.composite(img, bg_img, mask=img)
        draw = ImageDraw.Draw(img)

        if config.focusPoint.toggled:
            radius = config.focusPoint.radius
            color = config.focusPoint.colors[0]
            box = (
                self.width//2-radius, self.height//2-radius, self.width//2+radius, self.height//2+radius)
            draw.ellipse(box, fill=color)

        # Display the progress bar
        if self.debug:
            tt = t % self.trial_length
            r1 = tt / self.trial_length

            draw.rectangle(
                (0, 0, self.width*r1, 10), outline='#D0104C')

            if tt > self.t1:
                r21 = self.t1 / self.trial_length
                r22 = min(tt, self.t2) / self.trial_length
                draw.rectangle(
                    (self.width*r21, 0, self.width*r22, 10), fill='#D0104C')

        return img


# %% ---- 2024-11-01 ------------------------
# Play ground


# %% ---- 2024-11-01 ------------------------
# Pending


# %% ---- 2024-11-01 ------------------------
# Pending
