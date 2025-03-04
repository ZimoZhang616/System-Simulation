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
EPS = 1e-6

''' ------------------------------------------------------------------------------- '''
''' Factory/Backend 后端工厂 '''
''' ------------------------------------------------------------------------------- '''

# Robot Policy
# DEFAULT: Robot-oriented, random choose a ready job
# R1: Robot-oriented, maximize robot utilization
# M1: Machine-oriented, maximize machine utilization
# J1: Job-oriented, maximize throughput
# K1: random assign to stalled jobs#
ROBOT_POLICY_NAME = 'DEFAULT' # random
#ROBOT_POLICY_NAME = 'DISTANCE'# the robot will search for the nearest workstation and get a random job from its output
#ROBOT_POLICY_NAME = 'DISTANCE_NEH'

# Workstation policy
# DEFAULT: give job to machine in order of increasing index
WORKSTATION_POLICY_NAME = 'RANDOM'
#WORKSTATION_POLICY_NAME = 'FIFO' # FIFO
#WORKSTATION_POLICY_NAME = 'NEH'

# Workstation/machine
NUM_WORKSTATIONS = 6
NUM_MACHINES_WORKSTATION = [6, 4, 6, 4, 4, 4]
WORKSTATION_POS = [(-50, 0), (-50, 150), (100, 150), (250, 150), (250, 0), (100, 0)]  # unit: feet
FACTORY_POS = (-200,75)
# Robot
NUM_ROBOTS = 5
ROBOT_SPEED = 5     # unit: feet per second

# Job
JOB_ARRIVAL_RATE = 40 / 3600    # number of arrival jobs per second
JOB_OUTPUT_RATE = 120 / (8 * 3600)  # number of job output target per second

NUM_JOB_TYPES = 3
JOB_ROUTING = [
    [3, 1, 6, 2, 5],
    [4, 1, 3],
    [6, 2, 5, 1, 4, 3],
]
JOB_TIME_GAMMA = 2
JOB_TIME_MEAN = [
    [0.25 * 3600, 0.15 * 3600, 0.20 * 3600, 0.10 * 3600, 0.30 * 3600],
    [0.15 * 3600, 0.20 * 3600, 0.30 * 3600],
    [0.25 * 3600, 0.15 * 3600, 0.10 * 3600, 0.35 * 3600, 0.20 * 3600, 0.20 * 3600],
]

JOB_GENERATE_SEED = 42
JOB_GENERATE_PROBABILITY = [0.3, 0.5, 0.2]
MAX_JOB_NUM = 300

# Timing
BACKEND_CYCLE_TIME = 5e-1       # unit: second
TOTAL_BACKEND_RUN_TIME = 3600*10     # unit: second

BACKEND_SPEED_RATIO = 400      # speed up ratio (仿真加速比率)

''' ------------------------------------------------------------------------------- '''
''' GUI/Frontend 前端界面 '''
''' ------------------------------------------------------------------------------- '''

# Timing
FRONTEND_CYCLE_TIME = 5e-2      # unit: second

# Window/screen
WORLD_WIDTH = 900       # real-world bounds, unit: feet
WORLD_HEIGHT = 900      # real-world bounds, unit: feet
SCREEN_WIDTH = 1600    # window size, unit: pixel
SCREEN_HEIGHT = 1000     # window size, unit: pixel

# Map real-world coordinates to screen pixels
def map_to_screen(pos):
    screen_x = int((pos[0] + WORLD_WIDTH / 2) / WORLD_WIDTH * SCREEN_WIDTH * 0.8) - 50
    screen_y = int((WORLD_HEIGHT/2 - pos[1]) / WORLD_HEIGHT * SCREEN_HEIGHT) * 0.6 + 320

    return screen_x, screen_y

ROBOT_DIAMETER = 40     # robot size, for display only, unit: pixel
STATION_WIDTH = 40     # station width, for display only, unit: pixel

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
