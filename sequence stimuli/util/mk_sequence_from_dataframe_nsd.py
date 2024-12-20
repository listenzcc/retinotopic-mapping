"""
File: mk_sequence_from_dataframe_nsd.py
Author: Chuncheng Zhang
Date: 2024-12-19
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Make the stimuli sequence from the given dataFrame.
    The images are specified to the nsd shared1000 dataset.

Functions:
    1. Requirements and constants
    2. Function and class
    3. Play ground
    4. Pending
    5. Pending
"""


# %% ---- 2024-12-19 ------------------------
# Requirements and constants
import random
import pandas as pd
from pathlib import Path
from . import logger, current_dir


# %% ---- 2024-12-19 ------------------------
# Function and class
nsd_shared1000_folder = current_dir.joinpath('img/nsd-shared1000')


def mk_sequence_from_dataframe_nsd(
        df: pd.DataFrame, mode: str, nsd_folder: Path = nsd_shared1000_folder) -> list:
    """
    Make the stimuli sequence from the given dataFrame.
    The images are specified to the nsd shared1000 dataset.

    Args:
        df, DataFrame: The dataFrame of stimuli images.
        mode, str: The mode of the image, 'colorful' or 'hed'.
        nsd_folder, Path: The folder of nsd shared1000 images.

    Returns:
        The sequence of stimuli.
    """

    nds_names = df['nsdName']

    if mode == 'colorful':
        sequence = [nsd_folder.joinpath(
            f'colorful/{name}.png') for name in nds_names]
    elif mode == 'hed':
        sequence = [nsd_folder.joinpath(
            f'hed/{name}.png') for name in nds_names]
    else:
        raise ValueError(f'Unknown mode: {mode}')
    logger.info(f'Made sequence in mode: {mode}')
    logger.debug(f'Sequence is {sequence}')

    random.shuffle(sequence)
    return sequence


# %% ---- 2024-12-19 ------------------------
# Play ground


# %% ---- 2024-12-19 ------------------------
# Pending


# %% ---- 2024-12-19 ------------------------
# Pending
