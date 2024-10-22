# global import
import os
import enum
import math
import numpy as np
import time
import random
from queue import Queue

import pygame

# Global Return
RTN_OK = 0
RTN_ERR = -1

''' ------------------------------------------------------------------------------- '''
''' Factory/Backend 后端工厂 '''
''' ------------------------------------------------------------------------------- '''

# Policy
# R1: Robot-oriented, maximize robot utilization
# M1: Machine-oriented, maximize machine utilization
# J1: Job-oriented, maximize throughput
# K1: random assign to stalled jobs
ROBOT_POLICY_NAME = 'DEFAULT'
# POLICY_NAME = 'NA'

WORKSTATION_POLICY_NAME = 'DEFAULT'

# Workstation/machine
NUM_WORKSTATIONS = 5
NUM_MACHINES_WORKSTATION = [3, 5, 3, 4, 2]
WORKSTATION_POS = [(-150, 0), (-150, 150), (0, 150), (150, 150), (150, 0)]  # unit: feet

# Robot
NUM_ROBOTS = 3
ROBOT_SPEED = 5     # unit: feet per second

# Job
JOB_ARRIVAL_RATE = 25 / 3600    # number of arrival jobs per second
JOB_OUTPUT_RATE = 120 / (8 * 3600)  # number of job output target per second

NUM_JOB_TYPES = 3
JOB_ROUTING = [
    [3, 1, 2, 5],
    [4, 1, 3],
    [2, 5, 1, 4, 3],
]
JOB_TIME_GAMMA = 2
JOB_MEAN_TIME = [
    [0.25 * 3600, 0.15 * 3600, 0.10 * 3600, 0.30 * 3600],
    [0.15 * 3600, 0.20 * 3600, 0.30 * 3600],
    [0.15 * 3600, 0.10 * 3600, 0.35 * 3600, 0.20 * 3600, 0.20 * 3600],
]
JOB_PROBABILITY = [0.3, 0.5, 0.2]
JOB_GENERATE_SEED = 42
MAX_JOB_NUM = 200

# Timing
BACKEND_CYCLE_TIME = 5e-2       # unit: second
TOTAL_BACKEND_RUN_TIME = 3600     # unit: second

BACKEND_SPEED_RATIO = 40      # speed up ratio (仿真加速比率)

''' ------------------------------------------------------------------------------- '''
''' GUI/Frontend 前端界面 '''
''' ------------------------------------------------------------------------------- '''

# Timing
FRONTEND_CYCLE_TIME = 2e-2      # unit: second

# Window/screen
WORLD_WIDTH = 600       # real-world bounds, unit: feet
WORLD_HEIGHT = 600      # real-world bounds, unit: feet
SCREEN_WIDTH = 1200    # window size, unit: pixel
SCREEN_HEIGHT = 800     # window size, unit: pixel

# Map real-world coordinates to screen pixels
def map_to_screen(pos):
    screen_x = int((pos[0] + WORLD_WIDTH / 2) / WORLD_WIDTH * SCREEN_WIDTH * 0.8) - 100
    screen_y = int((WORLD_HEIGHT/2 - pos[1]) / WORLD_HEIGHT * SCREEN_HEIGHT) * 0.6 + 250

    return screen_x, screen_y

ROBOT_DIAMETER = 40     # robot size, for display only, unit: pixel
STATION_WIDTH = 200     # station width, for display only, unit: pixel

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_YELLOW = (255, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_LIGHT_GREY = (211, 211, 211)
COLOR_LIGHT_BLUE = (173, 216, 230)  # Light blue for processing and queue
COLOR_ORANGE = (255, 165, 0)  # Orange for output and occupied

# Fonts
FONT_FAMILY = 'consolas'
FONT_SIZE = 18
