"""
File: app.py
Author: Chuncheng Zhang
Date: 2024-11-01
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    The application of sequence stimuli

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-11-01 ------------------------
# Requirements and constants
import sys
import argparse

from PyQt6.QtCore import Qt, QTimer
from util.display import SequenceStimuli
from util import logger, config


# %% ---- 2024-11-01 ------------------------
# Function and class
parser = argparse.ArgumentParser(
    description="Sequence stimuli application.")
parser.add_argument('-d', '--debug',
                    help='Enable debug display', action='store_true')
parser.add_argument('-w', '--wait',
                    help='Wait for start key press', action='store_true')
namespace = parser.parse_args()
logger.info(f'Using namespace: {namespace}')

# %% ---- 2024-11-01 ------------------------
# Play ground
if __name__ == "__main__":
    stimuli = SequenceStimuli(namespace.debug)

    # Setup the mapping into the main_loop
    stimuli.window.show()

    if not namespace.wait:
        stimuli.main_loop()

    def _on_timeout():
        stimuli.repaint()

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

            # The quite key is pressed, quit the app
            if enum.name == config.control.quitKeyName:
                stimuli.app.quit()

            # The start key is pressed, start the main loop
            if namespace.wait and enum.name == config.control.startKeyName:
                stimuli.main_loop()

        except Exception as err:
            logger.error(f'Key pressed but I got an error: {err}')

    def _about_to_quit():
        '''
        Safely quit
        '''
        stimuli.stop_running()
        logger.debug('Safely quit the application')
        return

    # Bind the _about_to_quit and _on_key_pressed methods
    stimuli.app.aboutToQuit.connect(_about_to_quit)
    stimuli.window.keyPressEvent = _on_key_pressed

    # Bind to the timer and run
    timer = QTimer()
    timer.timeout.connect(_on_timeout)
    timer.start()

    # Proper exit
    sys.exit(stimuli.app.exec())

# %% ---- 2024-11-01 ------------------------
# Pending


# %% ---- 2024-11-01 ------------------------
# Pending
