# Import necessary packages
from __future__ import annotations
from typing import List
from pathlib import Path
import logging
import random
import glob

import pygame
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_MINUS, K_EQUALS, K_ESCAPE, K_SPACE
from pygame.locals import KEYDOWN, VIDEORESIZE, QUIT

import pytmx
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


class Item (pygame.sprite.Sprite):

    def __init__(self, name, graphic_file, x, y):
        super().__init__()
        self.name = name
        self.image = load_image(graphic_file).convert_alpha()
        self._position = [x, y]
        self.rect = self.image.get_rect()

    @property
    def name(self) -> str:
        return self._name

    @property
    def visible(self) -> str:
        return self._visible
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @visible.setter
    def visible(self, value: bool) -> None:
        self._name = value


class Quest ():
    
    def __init__(self, name, location, item):
        self._name = name
        self._location = location
        self._item = item
        self._status = None
        self._future_status = None

    @property
    def future_status(self) -> int:
        return self._future_status
    
    @future_status.setter
    def future_status(self, value: int) -> None:
        self._future_status = value

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def location(self) -> str:
        return self._location
    
    @property
    def item(self) -> Item:
        return self._item
    
    @property
    def status(self) -> bool:
        return self._status
    
    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @location.setter
    def location(self, value: str) -> None:
        self.location = value

    @item.setter
    def item(self, value: Item) -> None:
        self._item = value

    @status.setter
    def status(self, value: int) -> None:
        self._status = value


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

        self._talking = False
        self._talkingwho = None
        self._dialogs = {}

        self._quest = None

    @property
    def quest(self) -> str:
        return self._quest

    @quest.setter
    def quest(self, value: str) -> None:
        self._quest = value

    @property
    def talking(self) -> bool:
        return self._talking

    @talking.setter
    def talking(self, value: bool) -> None:
        self._talking = value

    @property
    def talkingwho(self) -> str:
        return self._talkingwho

    @talkingwho.setter
    def talkingwho(self, value: str) -> None:
        self._talkingwho = value

    @property
    def dialogs(self) -> str:
        return self._dialogs

    @dialogs.setter
    def dialogs(self, key: str, value: str) -> None:
        self._dialogs[key] = value

    @dialogs.setter
    def dialogs(self, value: dict) -> None:
        self._dialogs = value

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


class GameMap:
    """ This is the map class. 

    The GameMap class will allow us to load and track state for multiple maps.
    GameEngine will load and switch between the different GameMap instances
    throughout normal game play.

    We will track three different map constructs:

    * Zones - An area to contain an NPC
    * Walls - Areas that NPCs or our main player cannot go beyond
    * Exits - Areas that when crossed, take you to other locations
    """

    map_path = config.RESOURCE_DIR

    def __init__(self, map, screen, zoom=2, clamp_camera=False, characters=None, hero=None, hero_x=None, hero_y=None):

        self.screen = screen

        # load data from pytmx
        tmx_data = load_pygame(self.map_path.joinpath(map))   

        # setup level geometry with simple pygame rects, loaded from pytmx
        self.walls = []
        self.exits = []
        self.exit_objs = []
        self.zones = []
        self.zone_objs = []
        self.hero_start_postion = None

        # Placeholder for any dialog that needs to be displayed
        self._dialog = None

        # Initialize a container for any NPCs that may be on a given map
        self.characters = []

        @property
        def dialog(self) -> str:
            return self._dialog

        @dialog.setter
        def dialog(self, value) -> None:
            self._dialog = value
        
        # Sift through the object layers we are interested in and save 
        # those off in different lists so we can react to them later on.
        for layer in tmx_data.layers:
            if layer.name == 'Walls':
                for obj in layer:
                    self.walls.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            elif layer.name == 'Exits':
                for obj in layer:
                    self.exits.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                    self.exit_objs.append(obj)
            elif layer.name == 'Zones':
                for obj in layer:
                    self.zones.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                    self.zone_objs.append(obj)
            elif layer.name == 'Hero Start Position':
                for obj in layer:
                    self.hero_start_postion = (obj.x, obj.y)

        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(tmx_data)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            map_data, screen.get_size(), clamp_camera=clamp_camera, tall_sprites=1
        )

        self.map_layer.zoom = zoom

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

        # Instantiate our "hero" character
        self.hero = hero if hero else Character()

        if hero_x and hero_y:
            # Use the provided values to position our hero
            self.hero._position[0] = hero_x
            self.hero._position[1] = hero_y
        else:
            # put the hero in the center of the map
            self.hero.position = self.map_layer.map_rect.center

        # add our hero to the group
        self.group.add(self.hero)

        # Instantiate our NPCs if we have any
        if characters:
            self.add_characters(characters)

            for character in self.characters:
                self.group.add(character)

    @property
    def zoom(self):
        return self.map_layer.zoom

    @zoom.setter
    def zoom(self, value: int):
        self.map_layer.zoom = value

    @property
    def clamp_camera(self):
        return self.map_data.clamp_camera
    
    @clamp_camera.setter
    def clamp_camera(self, value: bool):
        self.map_layer.clamp_camera = value
    
    def add_characters(self, characters):
        for character in characters:
            # Instantiate a new NPC in the characters list
            self.characters.append(Character(name=character['name']))

            # Configure the character based on additional attributes
            self.characters[-1]._position[0] = character['x']
            self.characters[-1]._position[1] = character['y']
            self.characters[-1].dialogs = character['dialogs']

            self.group.add(self.characters[-1])

    def draw(self) -> None:

        # center the map/screen on our Hero
        self.group.center(self.hero.rect.center)

        # draw the map and all sprites
        self.group.draw(self.screen)

        # Draw the dialog box if we need one
        if self._dialog:
            d = self.text_speech('Script', 30, self._dialog, (255, 255, 255), (0, 0, 0), 800/2, 400/2, False)
            self.screen.blit(d[0], d[1])

    def text_speech(self, font: str, size: int, text: str, color, background, x, y, bold: bool):
        font = pygame.font.SysFont(font, size)
        font.set_bold(bold)
        textSurf = font.render(text, True, color).convert_alpha()
        textSize = textSurf.get_size()   
        bubbleSurf = pygame.Surface((textSize[0]*2., textSize[1]*2))
        bubbleRect = bubbleSurf.get_rect()
        bubbleSurf.fill(background)
        bubbleSurf.blit(textSurf, textSurf.get_rect(center=bubbleRect.center))
        bubbleRect.center = (x, y)
        return (bubbleSurf, bubbleRect)

    def move_characters(self) -> None:

        for character in self.characters:
            # If we are touching the player, we don't want to move so we can
            # give the player a chance to decide if they wish to interact with
            # the NPC
            if not character.rect.colliderect(self.hero.rect):
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

    def update(self, dt, current_map) -> str:

        map_name = current_map

        """Tasks that occur over time should be handled here"""
        self.group.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail

        # Temporary placeholder for dialog
        dialog = None

        for sprite in self.group.sprites():
            # Handle obstacle collisions for all sprites
            if sprite.feet.collidelist(self.walls) > -1:
                sprite.move_back(dt)

            if sprite.name == 'chewie_00':
                # Handle cases for the main player

                # Handle exit collisions
                exit_collision = sprite.feet.collidelist(self.exits)
                # Detected an exit collision and we're the hero
                if exit_collision > -1:
                    print('Exit collision value: {}. \t Exit portal type: {}'.format(exit_collision, self.exit_objs[exit_collision].type))
                    all_collisions = self.exits + self.walls
                    while sprite.feet.collidelist(all_collisions) > -1:
                        current_collision = sprite.feet.collidelist(all_collisions)
                        sprite._position[0] = all_collisions[current_collision].center[0] + ((all_collisions[current_collision].centerx - all_collisions[current_collision].left) * 1.5 * random.choice([-1, 1]))
                        sprite._position[1] = all_collisions[current_collision].center[1] + ((all_collisions[current_collision].centery - all_collisions[current_collision].top) * 1.5 * random.choice([-1, 1]))
                        sprite.update(dt)

                    map_name = self.exit_objs[exit_collision].name

            else:
                if self.hero.talking and not dialog:
                    if sprite.rect.colliderect(self.hero.rect):
                        self.hero.talkingwho = sprite.name

                        quest_name = sprite.name + '_quest'

                        if not self.hero.quest:
                            dialog = sprite.dialogs['hello']
                            self.hero.quest = quest_name
                            GameEngine.quests[self.hero.quest].future_status = 1
                        else:
                            if self.hero.quest == quest_name:
                                if GameEngine.quests[self.hero.quest].status == 1:
                                    dialog = sprite.dialogs['what']
                            else:
                                dialog = sprite.dialogs['goaway']

        if self.hero.talking and dialog:
            self._dialog = dialog
            dialog = None
        else:
            # self.hero.talking = False
            self.hero.talkingwho = None

        return map_name


class GameEngine:
    """This class is a basic game.

    This class will load data, create a pyscroll group, a hero object.
    It also reads input and moves the Hero around the map.
    Finally, it uses a pyscroll group to render the map and Hero.
    """

    map_path = config.RESOURCE_DIR

    quests = {}

    def __init__(self, screen: pygame.Surface, map="main_map.tmx") -> None:
        self.screen = screen

        # true while running
        self.running = False

        # Characters
        characters = [
            {
                "name": "chewie_04", 
                "x": 2240, 
                "y": 10044,
                "dialogs": {
                    "hello": "Hello world!",
                    "what": 'Go find my thing dummy.',
                    "salutation": "What's going on?",
                    'goaway': 'You look busy. Find me later.',
                    "bye": "Goodbye"
                }
            },
            {
                "name": "chewie_13", 
                "x": 4416, 
                "y": 9432,
                "dialogs": {
                    "hello": "Bon jour!",
                    "what": 'Rawrr rrr warrwrrr.',
                    "salutation": "Comment allez-vous?",
                    'goaway': 'Find me later dude.',
                    "bye": "Au revoir!"
                }
            },
        ]

        GameEngine.quests['chewie_04_quest'] = Quest('chewie04_quest', 'plains_portal.tmx', Item('Green Light Saber', 'light_saber.png', 400, 400))
        GameEngine.quests['chewie_13_quest'] = Quest('chewie13_quest', 'plains_portal.tmx', Item('Green Light Saber', 'light_saber.png', 400, 400))

        # Get a list of our maps
        maps = glob.glob('**/*.tmx', recursive=True)

        # Define a dictionary for our maps
        self.maps = {}
        self.map_names = []

        # Load the maps
        for map in maps:
            # Strip off the extraneous path information
            map_name = Path(map).name
            self.map_names.append(map_name)

            # Load the map into our dictionary
            self.maps[map_name] = GameMap(map_name, screen, hero=Character())

            # Load the maps with additional details
            if map_name == 'main_map.tmx':
                # Main map gets characters
                self.maps[map_name].add_characters(characters)
                self.maps[map_name].hero._position[0] = 2200
                self.maps[map_name].hero._position[1] = 10000
            else:
                self.maps[map_name].hero._position[0] = self.maps[map_name].hero_start_postion[0]
                self.maps[map_name].hero._position[1] = self.maps[map_name].hero_start_postion[1]
                self.maps[map_name].zoom = 1
                self.maps[map_name].clamp_camera = True

            # Set our inital map
            self.current_map = 'main_map.tmx'

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
                    self.maps[self.current_map].map_layer.zoom += 0.25

                elif event.key == K_MINUS:
                    value = self.maps[self.current_map].map_layer.zoom - 0.25
                    if value > 0:
                        self.maps[self.current_map].map_layer.zoom = value

                elif event.key == K_SPACE:
                    # Flip the talking bit
                    self.maps[self.current_map].hero.talking = not self.maps[self.current_map].hero.talking
                    if not self.maps[self.current_map].hero.talking:
                        self.maps[self.current_map].hero.talkingwho = None
                        self.maps[self.current_map]._dialog = None
                        ##
                        GameEngine.quests[self.maps[self.current_map].hero.quest].status = GameEngine.quests[self.maps[self.current_map].hero.quest].future_status

            # this will be handled if the window is resized
            elif event.type == VIDEORESIZE:
                self.screen = init_screen(event.w, event.h)
                self.maps[self.current_map].map_layer.set_size((event.w, event.h))

            event = poll()

        # using get_pressed is slightly less accurate than testing for events
        # but is much easier to use.
        pressed = pygame.key.get_pressed()

        if pressed[K_UP]:
            self.maps[self.current_map].hero.velocity[1] = -config.MOVE_SPEED
        elif pressed[K_DOWN]:
            self.maps[self.current_map].hero.velocity[1] = config.MOVE_SPEED
        else:
            self.maps[self.current_map].hero.velocity[1] = 0

        if pressed[K_LEFT]:
            self.maps[self.current_map].hero.velocity[0] = -config.MOVE_SPEED
        elif pressed[K_RIGHT]:
            self.maps[self.current_map].hero.velocity[0] = config.MOVE_SPEED
        else:
            self.maps[self.current_map].hero.velocity[0] = 0

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

                self.handle_input()
                self.maps[self.current_map].move_characters()

                new_map = self.maps[self.current_map].update(dt, self.current_map)
                if new_map != self.current_map:
                    if self.maps[new_map].hero_start_postion:
                        self.maps[new_map].hero._position[0] = self.maps[new_map].hero_start_postion[0]
                        self.maps[new_map].hero._position[1] = self.maps[new_map].hero_start_postion[1]

                    self.current_map = new_map

                self.maps[self.current_map].draw()
                pygame.display.flip()

        except KeyboardInterrupt:
            self.running = False
