""" runtime.py - Central bootstrap and config for RTSGame

This file will execute the runnable components of the game and provide
a location for configuration variables.

"""

# Import necessary packages
from __future__ import annotations
import logging

import pygame
import objects


# Package local variables
log = logging.getLogger(__name__)


# simple wrapper to keep the screen resizable
def init_screen(width: int, height: int) -> pygame.Surface:
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    return screen


def run():
	log.info("Entering the runtime.")

	pygame.init()
	pygame.font.init()
	pygame.display.set_caption("Real Time Strategy (rtsgame)")

	screen = init_screen(800, 600)

	try:
		engine = objects.GameEngine(screen)
		engine.run()
	except KeyboardInterrupt:
		pass
	finally:
		pygame.quit()

