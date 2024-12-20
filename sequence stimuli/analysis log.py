"""
File: analysis log.py
Author: Chuncheng Zhang
Date: 2024-12-19
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


# %% ---- 2024-12-19 ------------------------
# Requirements and constants
import time
import pandas as pd
from dateutil.parser import isoparse


# %% ---- 2024-12-19 ------------------------
# Function and class
lines = open('./log/sequence stimuli.log').readlines()
lines = [e for e in lines if 'util.display:get_and_prepare_img:354 - Display img:' in e]
lines

# %%

data = []
for line in lines:
    s = line.split('|')[0].strip()
    timestamp = isoparse(s).timestamp()
    data.append(timestamp)
data = pd.DataFrame(data, columns=['ts'])
data['delay'] = data['ts'] - data.loc[0, 'ts']
display(data)

data.loc[150]


# %% ---- 2024-12-19 ------------------------
# Play ground


# %% ---- 2024-12-19 ------------------------
# Pending


# %% ---- 2024-12-19 ------------------------
# Pending
