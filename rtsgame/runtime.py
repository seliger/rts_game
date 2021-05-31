""" runtime.py - Central engine for RTSGame

This file will implement the runnable components of the game,
including the primary event loop.

"""

# Import necessary packages
from __future__ import annotations
import logging

from game import RTSGame

# Package local variables
log = logging.getLogger(__name__)

def run():
	log.info("Entering the runtime.")
	# RTSGame is a class that stores our game configuration, etc.
	game = RTSGame()
