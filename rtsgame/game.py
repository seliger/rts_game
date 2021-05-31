# Import necessary packages
from __future__ import annotations
from pathlib import Path
import logging

# Package local variables
log = logging.getLogger(__name__)


class RTSGame:
	def __init__(self):
		# define configuration variables here
		self.CURRENT_DIR = Path(__file__).parent
		self.RESOURCE_DIR = self.CURRENT_DIR.joinpath("data")
		self.MOVE_SPEED = 200  # pixels per second

		log.info("Current working directory is {}".format(self.CURRENT_DIR))
		log.info("Resource directory is {}".format(self.RESOURCE_DIR))


