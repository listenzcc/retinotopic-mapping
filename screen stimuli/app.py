"""
File: app.py
Author: Chuncheng Zhang
Date: 2024-10-28
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    The application of retinotopic mapping

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
import argparse

from PyQt6.QtCore import Qt, QTimer
from util.display import EccentricityMapping, PolarAngleMapping
from util import logger


# %% ---- 2024-10-28 ------------------------
# Function and class
parser = argparse.ArgumentParser(
    description="Retinotopic mapping application.")
parser.add_argument('-e', '--eccentricity',
                    help='Use eccentricity mapping', action='store_true')
parser.add_argument('-p', '--polarAngle',
                    help='Use polarAngle mapping', action='store_true')
parser.add_argument('-d', '--debug',
                    help='Enable debug display', action='store_true')
namespace = parser.parse_args()
print(namespace)

assert not all(
    (namespace.eccentricity, namespace.polarAngle)), 'Can not use both --eccentricity and --polarAngle'

# %% ---- 2024-10-28 ------------------------
# Play ground
if __name__ == "__main__":
    # Initialize the mapping
    if namespace.eccentricity:
        mapping = EccentricityMapping(namespace.debug)

    if namespace.polarAngle:
        mapping = PolarAngleMapping(namespace.debug)

    # Setup the mapping into the main_loop
    mapping.window.show()
    mapping.main_loop()

    def _on_timeout():
        mapping.repaint()

    def _on_key_pressed(event):
        '''
        Handle the key pressed event.

        Args:
            - event: The pressed event.
        '''

        try:
            key = event.key()
            enum = Qt.Key(key)
            logger.debug(f'Key pressed: {key}, {enum.name}')

            # If esc is pressed, quit the app
            if enum.name == 'Key_Escape':
                mapping.app.quit()

        except Exception as err:
            logger.error(f'Key pressed but I got an error: {err}')

    def _about_to_quit():
        '''
        Safely quit
        '''
        logger.debug('Safely quit the application')
        return

    # Bind the _about_to_quit and _on_key_pressed methods
    mapping.app.aboutToQuit.connect(_about_to_quit)
    mapping.window.keyPressEvent = _on_key_pressed

    # Bind to the timer and run
    timer = QTimer()
    timer.timeout.connect(_on_timeout)
    timer.start()

    # Proper exit
    sys.exit(mapping.app.exec())

# %% ---- 2024-10-28 ------------------------
# Pending


# %% ---- 2024-10-28 ------------------------
# Pending
