#!/usr/bin/env python

import asyncio
import random

import click

from . import Terminal64
from .cart import SummerCart64
from .game import *

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
        self.sprites = [self.n64brew_sprite, self.tiles_sprite]

        self.n64brew_entity = N64BrewEntity()
        self.tiles_entity = TilesEntity()
        self.entities = [self.tiles_entity, self.n64brew_entity]

        self.ready()

    def loop(self):
        self.tiles_entity.change()

async def amain(uart):
    cart = await SummerCart64.connect(uart)
    tile_demo = TileDemo(cart)
    await tile_demo.run()

@click.command
@click.argument('uart', default='/dev/ttyUSB0')
def main(uart):
    try:
        asyncio.run(amain(uart))
    except KeyboardInterrupt:
        pass
