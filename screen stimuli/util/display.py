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
import contextlib

import numpy as np

from PIL import Image, ImageDraw
from PIL.ImageQt import ImageQt

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QApplication, QLabel

from rich import print
from threading import Thread, RLock

from . import logger, config, current_dir

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


class EccentricityMapping(OnScreenDisplay):
    def __init__(self, debug=False):
        """
        Initialize the EccentricityMapping class, which inherits from OnScreenDisplay.

        This constructor calls the parent class's constructor (__init__ method) using the super() function.
        It does not take any parameters and does not return any value.

        The purpose of this constructor is to establish the inheritance relationship between the
        EccentricityMapping class and the OnScreenDisplay class, ensuring that the EccentricityMapping
        class inherits all the attributes and methods of the OnScreenDisplay class.
        """
        super().__init__()
        self.place_prompt_img()
        self.debug = debug

    def place_prompt_img(self):
        img = Image.open(
            current_dir.joinpath(config.prompt.img)).convert('RGBA')
        self.place_img(img)
        return

    def generate_img(self, t: float) -> Image.Image:
        """
        Generate an image for the eccentricity mapping display.

        This function generates an image based on the current time (t) and the configuration settings.
        The image is created using the PIL library and represents a ring with alternating colors.
        The ring's size, color, and position are determined by the configuration settings.

        Parameters:
        t (float): The current time in seconds.

        Returns:
        Image.Image: The generated image for the eccentricity mapping display.
        """
        # Get the configuration object
        cem = config.eccentricityMapping
        ccb = config.checkboxTexture

        # The r_center is the center of the ring.
        # The r_min, r_max is the inner and outer boundaries.
        r_center = cem.minRadius + ((t % cem.duration) / cem.duration) * \
            (cem.maxRadius - cem.minRadius)
        r_max = r_center + cem.width/2
        r_min = r_center - cem.width/2

        # Generate the image and its drawing context.
        # The initializing color is (0, 0, 0, 0) for all the pixels
        mat = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        img = Image.fromarray(mat.astype(np.uint8)+100, mode='RGBA')
        draw = ImageDraw.Draw(img)

        # The current color value (v) of sin functional,
        # and u is its reverse
        v = np.uint8((np.sin(ccb.flickingRate*t*np.pi*2)+1)*0.5*255)
        u = np.uint8(255-v)

        # Center of the ring
        cx = self.width / 2
        cy = self.height / 2

        # The arc block size.
        # Think it as the earth, the arc blocks are segmented by the longitude and latitude.
        arc_length = 360 / ccb.numInLongitude
        arc_width = (cem.maxRadius - cem.minRadius) / ccb.numInLatitude

        # The draw.arc box means the ring NEVER exceed the box,
        # or, the arc_width grows inside.
        # The r refers the bounding box size of the "narrow" arc block.
        # The angle refers the start angle of the arc block.
        for j, r in enumerate(np.linspace(cem.minRadius, cem.maxRadius+arc_width*2, 2+ccb.numInLatitude, endpoint=False)):
            # Not draw if the r is small and outside the ring range.
            if r < r_min:
                continue

            # Not draw if the r is large and outside the ring range.
            if r-arc_width > r_max:
                continue

            # Initialize as the NORMAL condition
            w = arc_width
            box = (cx-r, cy-r, cx+r, cy+r)

            # Shrink the width in the most inner blocks
            if r - arc_width < r_min:
                w = r - r_min
            # Shrink the width and shrink the box in the most outer blocks.
            # Restrict the s + w = arc_width to prevent blinking the edge.
            elif r > r_max and r-arc_width < r_max:
                w = int(arc_width-(r-r_max))
                s = arc_width - w
                box = (cx-r+s, cy-r+s, cx+r-s, cy+r-s)

            # Safely convert the width (w)
            w = int(w)

            # Draw the arc blocks one-by-one with DIFFERENT colors
            for i, angle in enumerate(np.linspace(0, 360, ccb.numInLongitude, endpoint=False)):
                if i % 2 == j % 2:
                    fill = (v, v, v, 255)
                else:
                    fill = (u, u, u, 255)
                draw.arc(
                    box, start=angle, end=angle+arc_length, width=w, fill=fill)

        if self.debug:
            box = (cx-r_center, cy-r_center, cx+r_center, cy+r_center)
            draw.arc(
                box, start=0, end=360, width=2, fill=(255, 0, 0, 255))

            if r_min > 0:
                box = (cx-r_min, cy-r_min, cx+r_min, cy+r_min)
                draw.arc(
                    box, start=0, end=360, width=2, fill=(0, 255, 0, 255))

            box = (cx-r_max, cy-r_max, cx+r_max, cy+r_max)
            draw.arc(
                box, start=0, end=360, width=2, fill=(0, 255, 0, 255))

        return img


class PolarAngleMapping(OnScreenDisplay):
    def __init__(self, debug=False):
        super().__init__()
        self.place_prompt_img()
        self.debug = debug

    def place_prompt_img(self):
        img = Image.open(
            current_dir.joinpath(config.prompt.img)).convert('RGBA')
        self.place_img(img)
        return

    def generate_img(self, t: float) -> Image.Image:
        # Get the configuration object
        cpam = config.polarAngleMapping
        ccb = config.checkboxTexture

        # The a_center is the center of the spin.
        # The a_min, a_max are the front and back boundaries.
        a_center = ((t % cpam.duration)/cpam.duration) * 360
        a_min = a_center - cpam.width/2
        a_max = a_center + cpam.width/2

        # Generate the image and its drawing context.
        # The initializing color is (0, 0, 0, 0) for all the pixels
        mat = np.zeros((self.height, self.width, 4), dtype=np.uint8)
        img = Image.fromarray(mat.astype(np.uint8)+100, mode='RGBA')
        draw = ImageDraw.Draw(img)

        # The current color value (v) of sin functional,
        # and u is its reverse
        v = np.uint8((np.sin(ccb.flickingRate*t*np.pi*2)+1)*0.5*255)
        u = np.uint8(255-v)

        # Center of the ring
        cx = self.width / 2
        cy = self.height / 2

        # The arc block size
        # Think it as the earth, the arc blocks are segmented by the longitude and latitude.
        arc_length = 360 / ccb.numInLongitude
        arc_width = (cpam.maxRadius - cpam.minRadius) / ccb.numInLatitude
        # Find the nearest back edge with the a_min,
        # in case it is negative value,
        # or the a_max exceeds 360 degrees.
        offset = a_min // arc_length

        # The draw.arc box means the ring NEVER exceed the box,
        # or, the arc_width grows inside.
        # The r refers the bounding box size of the "narrow" arc block.
        # The angle refers the start angle of the arc block.
        for j, r in enumerate(np.linspace(cpam.minRadius, cpam.maxRadius, ccb.numInLatitude, endpoint=False)):
            w = int(arc_width)
            box = (cx-r, cy-r, cx+r, cy+r)

            # Draw the arc blocks one-by-one with DIFFERENT colors
            for angle in np.linspace(0, 360, ccb.numInLongitude, endpoint=False):
                angle += offset * arc_length
                i = angle // arc_length

                # Not draw if angle exceeds a_max
                if angle > a_max:
                    continue

                # Not draw if angle belows a_min
                if angle+arc_length < a_min:
                    continue

                # Setup start and end angles with arc blocks INSIDE spin
                start = angle
                end = angle + arc_length

                # Shrink end if front edge exceeds
                if angle + arc_length > a_max:
                    end = a_max

                # Increase start if tail edge exceeds
                if angle < a_min:
                    start = a_min

                if i % 2 == j % 2:
                    fill = (v, v, v, 255)
                else:
                    fill = (u, u, u, 255)
                draw.arc(
                    box, start=start, end=end, width=w, fill=fill)

            if self.debug:
                draw.arc(
                    box, start=a_min, end=a_max, width=2, fill=(255, 0, 0, 255))

        return img

# %% ---- 2024-10-28 ------------------------
# Play ground


# %% ---- 2024-10-28 ------------------------
# Pending


# %% ---- 2024-10-28 ------------------------
# Pending
