#!/usr/bin/env python

import random
import sys

from game import Entity, Game, Sprite

display_width = 320
display_height = 240

class N64BrewEntity(Entity):
    def __init__(self):
        super().__init__()
        self.type = 'sprite'
        self.idx = 0
        self.x = display_width / 2 - 64 / 2
        self.y = display_height / 2 - 96 / 2

class TilesEntity(Entity):
    def __init__(self):
        super().__init__()
        self.type='sprite'
        self.idx = 1
        self.x = display_width / 2 - 32 / 2
        self.y = display_height / 2 - 32 / 2

    def change(self):
        self.tile = random.randint(0, 3)
        self.degrees = random.randint(0, 359)

class Stress(Game):
    def setup(self):
        self.n64brew_sprite = Sprite('filesystem/n64brew.sprite')
        self.tiles_sprite = Sprite('filesystem/tiles.sprite')
        self.n64brew_entity = N64BrewEntity()
        self.tiles_entity = TilesEntity()
        self.restart()

    def loop(self):
        self.tiles_entity.change()

    def restart(self):
        self.reset()
        self.sprites = [self.n64brew_sprite, self.tiles_sprite]
        self.entities = [self.n64brew_entity, self.tiles_entity]
        self.ready()

if __name__ == '__main__':
    try:
        port = sys.argv[1]
    except:
        port = '/dev/ttyUSB0'

    pong = Stress(port)
    pong.run()
