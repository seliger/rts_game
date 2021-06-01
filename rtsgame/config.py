""" config.py - Constants and other configuration.

"""


# Import necessary packages
from __future__ import annotations
from pathlib import Path


# Constants
CURRENT_DIR = Path(__file__).parent
RESOURCE_DIR = CURRENT_DIR.joinpath("data")
MOVE_SPEED = 200  # pixels per second