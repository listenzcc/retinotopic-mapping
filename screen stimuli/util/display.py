"""
File: displayer.py
Author: Chuncheng Zhang
Date: 2024-10-28
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Qt6 on screen display for retinotopic mapping.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-10-28 ------------------------
# Requirements and constants
import sys
import time
import itertools
import contextlib

import numpy as np

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL.ImageQt import ImageQt

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

from pathlib import Path
from omegaconf import OmegaConf
from rich import print
from threading import Thread, RLock

from . import logger, config


# %% ---- 2024-10-28 ------------------------
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
        self._rlock.acquire()
        try:
            yield
        finally:
            self._rlock.release()

    def repaint(self):
        with self.acquire_lock():
            if pixmap := self.pixmap:
                self.pixmap_container.setPixmap(pixmap)
        return

    def main_loop(self):
        Thread(target=self._main_loop, daemon=True).start()

    def _main_loop(self):
        self.running = True
        tic = time.time()
        i = 0
        while self.running:
            i += 1
            t = time.time()-tic
            img = self.generate_img(t)
            with self.acquire_lock():
                self.pixmap = QPixmap.fromImage(ImageQt(img))
            time.sleep(0.01)
            if i % 10 == 0:
                print(f'Frame rate: {i/t:0.2f}')


class EccentricityMapping(OnScreenDisplay):
    def __init__(self):
        super().__init__()

        cem = config.eccentricityMapping
        cb = config.checkbox

        width = self.width
        height = self.height

        mgx, mgy = np.meshgrid(
            np.linspace(-width/2, width/2, width),
            np.linspace(-height/2, height/2, height))

        r = np.sqrt(mgx**2 + mgy**2)
        mr = ((r-cem.minRadius) // ((cem.maxRadius -
                                    cem.minRadius)/cb.numInLatitude)) % 2

        a = (np.atan2(mgy, mgx) / np.pi + 1) * 0.5 * cb.numInLongitude
        ma = a.astype(np.int8) % 2

        self.mgx = mgx
        self.mgy = mgy
        self.r = r
        self.mr = mr
        self.ma = ma

    def generate_img(self, t: float):
        cem = config.eccentricityMapping
        cb = config.checkbox

        r_center = cem.minRadius + ((t % cem.duration) / cem.duration) * \
            (cem.maxRadius - cem.minRadius)
        r_min = r_center - cem.width/2
        r_max = r_center + cem.width/2

        width = self.width
        height = self.height

        mat = np.zeros((height, width, 4), dtype=np.uint8)

        r = self.r
        mr = self.mr
        ma = self.ma

        m1 = r < r_max
        m2 = r > r_min
        m = m1 * m2

        v = np.uint8((np.sin(cb.flickingRate*t)+1)*0.5*255)

        mat[m] = (255-v)
        mat[m*(mr+ma == 1)] = v

        img = Image.fromarray(mat.astype(np.uint8), mode='RGBA')
        # img = img.resize((self.width, self.height))
        img = img.filter(ImageFilter.SMOOTH)
        return img

# %% ---- 2024-10-28 ------------------------
# Play ground


# %% ---- 2024-10-28 ------------------------
# Pending


# %% ---- 2024-10-28 ------------------------
# Pending
