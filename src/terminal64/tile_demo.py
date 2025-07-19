#!/usr/bin/env python

import random

import click

from .games import SpriteEntity, Game, Sprite

display_width = 320
display_height = 240

class N64BrewEntity(SpriteEntity):
    def __init__(self):
        super().__init__()
        self.index = 0
        self.x = display_width / 2 - 64 / 2
        self.y = display_height / 2 - 96 / 2

class TilesEntity(SpriteEntity):
    def __init__(self):
        super().__init__()
        self.index = 1
        self.x = display_width / 2 - 32 / 2 + 16
        self.y = display_height / 2 - 32 / 2 + 16
        self.cx = 16
        self.cy = 16

    def change(self):
        self.tile = random.randint(0, 3)
        self.scale_x = 8
        self.scale_y = 8
        self.theta = random.vonmisesvariate(0, 0)

class TileDemo(Game):
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
        self.entities = [self.tiles_entity, self.n64brew_entity]
        self.ready()

@click.command
@click.argument('port', default='/dev/ttyUSB0')
def main(port):
    TileDemo(port).run()
