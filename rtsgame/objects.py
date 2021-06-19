# Import necessary packages
from __future__ import annotations
from typing import List
from pathlib import Path
import logging
import random

import pygame
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_MINUS, K_EQUALS, K_ESCAPE
from pygame.locals import KEYDOWN, VIDEORESIZE, QUIT
from pytmx.util_pygame import load_pygame

import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup

import config

# Package local variables
log = logging.getLogger(__name__)

# simple wrapper to keep the screen resizable
def init_screen(width: int, height: int) -> pygame.Surface:
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    return screen


# make loading images a little easier
def load_image(filename: str) -> pygame.Surface:
    log.info("Preparing to load image: {}".format(str(config.RESOURCE_DIR.joinpath(filename))))
    return pygame.image.load(str(config.RESOURCE_DIR.joinpath(filename)))


class GameConfig:
    def __init__(self):

        # define configuration variables here
        log.info("Current working directory is {}".format(self.CURRENT_DIR))
        log.info("Resource directory is {}".format(self.RESOURCE_DIR))

class Character (pygame.sprite.Sprite):
    """Character Class - A playable character/person in the game.

    The Character has three collision rects, one for the whole sprite "rect" and
    "old_rect", and another to check collisions with walls, called "feet".

    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down'
    as integers, the sprite would move faster moving left or up.

    Feet is 1/2 as wide as the normal rect, and 8 pixels tall.  This size size
    allows the top of the sprite to overlap walls.  The feet rect is used for
    collisions, while the 'rect' rect is used for drawing.

    There is also an old_rect that is used to reposition the sprite if it
    collides with level walls.
    """

    def __init__(self, name="chewie_00") -> None:
        super().__init__()
        self.name = name
        self.moving_direction = 0
        self.image = load_image(Path('sprites').joinpath(name + '.png')).convert_alpha()
        self.velocity = [0, 0]
        self._position = [0.0, 0.0]
        self._old_position = self.position
        self.rect = self.image.get_rect()
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 15)

    @property
    def position(self) -> List[float]:
        return list(self._position)

    @position.setter
    def position(self, value: List[float]) -> None:
        self._position = list(value)

    def update(self, dt: float) -> None:
        self._old_position = self._position[:]
        self._position[0] += self.velocity[0] * dt
        self._position[1] += self.velocity[1] * dt
        self.rect.topleft = self._position
        self.feet.midbottom = self.rect.midbottom

    def move_back(self, dt: float) -> None:
        """If called after an update, the sprite can move back"""
        self._position = self._old_position
        self.rect.topleft = self._position
        self.feet.midbottom = self.rect.midbottom


class GameEngine:
    """This class is a basic game.

    This class will load data, create a pyscroll group, a hero object.
    It also reads input and moves the Hero around the map.
    Finally, it uses a pyscroll group to render the map and Hero.
    """

    map_path = config.RESOURCE_DIR

    def __init__(self, screen: pygame.Surface, map="main_map.tmx") -> None:
        self.screen = screen

        # true while running
        self.running = False

        # load data from pytmx
        tmx_data = load_pygame(self.map_path.joinpath(map))   

        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = []
        self.portals = []
        self.portal_objs = []

        # Initalize a list for all of our non-player characters (NPCs)
        self.characters = []

        # Sift through the object layers we are interested in and save 
        # those off in different lists so we can react to them later on.
        for layer in tmx_data.layers:
            if layer.name == 'Walls':
                for obj in layer:
                    self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            elif layer.name == 'Portals':
                for obj in layer:
                    self.portals.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                    self.portal_objs.append(obj)
            elif layer.name == 'Background':
                self.background = layer.image
                print(self.background)

        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(tmx_data)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            map_data, screen.get_size(), clamp_camera=False, tall_sprites=1
        )
        self.map_layer.zoom = 2

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

        # Instantiate our "hero" character
        self.hero = Character()
        
        # Characters
        characters = [
            {"name": "chewie_04", "x": 2240, "y": 10044},
            {"name": "chewie_13", "x": 4416, "y": 9432},
        ]

        # Instantiate our NPCs
        self.add_characters(characters)

        # put the hero in the center of the map
        # self.hero.position = self.map_layer.map_rect.center
        self.hero._position[0] = 2300
        self.hero._position[1] = 10000

        for character in self.characters:
            self.group.add(character)

        # add our hero to the group
        self.group.add(self.hero)

    def add_characters(self, characters):
        log.info('Entering add_characters()')
        for character in characters:
            # Instantiate a new NPC in the characters list
            self.characters.append(Character(name=character['name']))

            # Configure the character based on additional attributes
            self.characters[-1]._position[0] = character['x']
            self.characters[-1]._position[1] = character['y']

    def draw(self) -> None:

        # center the map/screen on our Hero
        self.group.center(self.hero.rect.center)

        # draw the map and all sprites
        self.group.draw(self.screen)

    def move_characters(self) -> None:
        for character in self.characters:
            # Roll the dice to see if we move or not
            # If we move, randomly set a direction
            if random.randint(0, 100) < 65:
                character.moving_direction = 0
            else:
                character.moving_direction = random.choice([1, 2, 3, 4])

            # Randomly set or unset the trajectory of the sprite based
            # on the previously set direction
            if random.randint(0, 150) == 0:
                if character.moving_direction == 4:
                    character.velocity[0] = config.MOVE_SPEED
                elif character.moving_direction == 3:
                    character.velocity[0] = -config.MOVE_SPEED  
                else:
                    character.velocity[0] = 0

                if character.moving_direction == 2:
                    character.velocity[1] = config.MOVE_SPEED
                elif character.moving_direction == 1:
                    character.velocity[1] = -config.MOVE_SPEED
                else:
                    character.velocity[1] = 0

    def handle_input(self) -> None:
        """Handle pygame input events"""
        poll = pygame.event.poll

        event = poll()
        while event:
            if event.type == QUIT:
                self.running = False
                break

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    break

                elif event.key == K_EQUALS:
                    self.map_layer.zoom += 0.25

                elif event.key == K_MINUS:
                    value = self.map_layer.zoom - 0.25
                    if value > 0:
                        self.map_layer.zoom = value

            # this will be handled if the window is resized
            elif event.type == VIDEORESIZE:
                self.screen = init_screen(event.w, event.h)
                self.map_layer.set_size((event.w, event.h))

            event = poll()

        # using get_pressed is slightly less accurate than testing for events
        # but is much easier to use.
        pressed = pygame.key.get_pressed()
        if pressed[K_UP]:
            self.hero.velocity[1] = -config.MOVE_SPEED
        elif pressed[K_DOWN]:
            self.hero.velocity[1] = config.MOVE_SPEED
        else:
            self.hero.velocity[1] = 0

        if pressed[K_LEFT]:
            self.hero.velocity[0] = -config.MOVE_SPEED
        elif pressed[K_RIGHT]:
            self.hero.velocity[0] = config.MOVE_SPEED
        else:
            self.hero.velocity[0] = 0

    def update(self, dt):
        """Tasks that occur over time should be handled here"""
        self.group.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        for sprite in self.group.sprites():
            # Handle obstacle collisions
            if sprite.feet.collidelist(self.walls) > -1:
                sprite.move_back(dt)

            # Handle portal collisions
            portal_collision = sprite.feet.collidelist(self.portals)
            # if portal_collision > -1:
            #     print(self.portal_objs[portal_collision].name)
            #     portal = GameEngine(self.screen, 'plains_portal.tmx')
            #     portal.run()

    def run(self):
        """Run the game loop"""
        clock = pygame.time.Clock()
        self.running = True

        from collections import deque

        times = deque(maxlen=30)

        try:
            while self.running:
                dt = clock.tick() / 1000.0
                times.append(clock.get_fps())

                # possible move_characters()?
                self.handle_input()
                self.move_characters()
                # possible move_characters()? -- pick one
                self.update(dt)
                self.draw()
                pygame.display.flip()

        except KeyboardInterrupt:
            self.running = False
