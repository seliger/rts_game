# Import Modules
import pgzrun

# Define constants
WIDTH = 800
HEIGHT = 600
CENTER_X = WIDTH / 2
CENTER_Y = HEIGHT / 2
CENTER = (CENTER_X, CENTER_Y)
FONT_COLOR = (0, 0, 0)

# State tracking variables
game_over = False
game_complete = False


# This is our main drawing method
def draw():
    # Clear the screen and draw the map
    screen.clear()
    screen.blit('main_map', (0, 0))


# Initialize and run Pygame Zero (start the game)
pgzrun.go()
