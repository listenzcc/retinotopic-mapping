"""
File: __init__.py
Author: Chuncheng Zhang
Date: 2024-11-01
Copyright & Email: chuncheng.zhang@ia.ac.cn

Purpose:
    Amazing things

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

from pathlib import Path
from omegaconf import OmegaConf
from loguru import logger

current_dir = Path(sys.argv[0]).parent
logger.add(current_dir.joinpath('log/sequence stimuli.log'), rotation='5MB')
logger.info(f'Running in current directory: {current_dir}')

config = OmegaConf.load(current_dir.joinpath('config.yaml'))
logger.debug(f'Using config: {config}')

# %% ---- 2024-11-01 ------------------------
# Function and class


# %% ---- 2024-11-01 ------------------------
# Play ground


# %% ---- 2024-11-01 ------------------------
# Pending


# %% ---- 2024-11-01 ------------------------
# Pending
