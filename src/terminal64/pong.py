#!/usr/bin/env python

import asyncio
import random

import click

from .cart import SummerCart64
from .game import *

def clamp(value, min_, max_):
    return min(max_, max(min_, value))

class Paddle(RectangleEntity):
    def __init__(self, player):
        super().__init__()
        self.color = (0xFF, 0xFF, 0xFF)
        self.size = 0.25
        self.width = 5
        offset = 10
        if player == 0:
            self.x = offset
        elif player == 1:
            self.x = disp_width - self.width - offset
        self.pos = 0

    @property
    def pos(self):
        return self.y * 2 / (disp_height - self.height) - 1
    @pos.setter
    def pos(self, value):
        self.y = (value + 1) / 2 * (disp_height - self.height)

    @property
    def size(self):
        return disp_height / self.height
    @pos.setter
    def size(self, value):
        self.height = disp_height * value

class Ball(CircleEntity):
    def __init__(self, radius):
        super().__init__()
        self.color = (0xFF, 0x00, 0x00)
        self.radius = radius

class Score(TextEntity):
    def __init__(self):
        super().__init__()
        self.color = (0xFF, 0xFF, 0x00)
        self.y = 16
        self.reset()

    def reset(self):
        self.score = [0, 0]
        self.update()

    def increment(self, player):
        self.score[player] += 1
        self.update()

    def update(self):
        self.string = f'{self.score[0]}:{self.score[1]}'
        self.x = disp_width / 2 - len(self.string) * 8 / 2

class Pong(Game):
    def setup(self):
        self.score = Score()
        self.ball = Ball(4)
        self.paddle = [Paddle(0), Paddle(1)]
        self.restart()

    def loop(self):
        self.paddle[1].pos = self.ball.y / 240 * 2 - 1

        self.ball.x = clamp(self.ball.x + self.delta_x, 0, disp_width - self.ball.diameter - 1)
        self.ball.y = clamp(self.ball.y + self.delta_y, 0, disp_height - self.ball.diameter- 1)

        if collision(self.ball, self.paddle[0]):
            self.delta_x = 3
        elif collision(self.ball, self.paddle[1]):
            self.delta_x = -3
        elif self.ball.y == 0 or self.ball.y == disp_height - self.ball.diameter - 1:
            self.delta_y = -self.delta_y

        if self.ball.x == 0:
            self.score.increment(1)
            self.restart(1)
        elif self.ball.x == disp_width - self.ball.diameter - 1:
            self.score.increment(0)
            self.restart(0)

    def handle_input(self, inputs):
        pos = clamp(inputs.stick_y / -72.0, -1.0, 1.0)
        self.paddle[0].pos = pos

    def restart(self, winner=1):
        self.reset()
        self.entities = [self.score, self.ball] + self.paddle
        for entity in self.entities:
            entity._dirty = True
        self.ball.x = disp_width / 2 - self.ball.radius / 2
        self.ball.y = disp_height / 2 - self.ball.radius / 2
        self.delta_x = 3 if winner == 1 else -3
        self.delta_y = random.choice([3, -3])
        self.ready()

async def amain(uart):
    cart = await SummerCart64.connect(uart)
    tile_demo = Pong(cart)
    await tile_demo.run()

@click.command
@click.argument('uart', default='/dev/ttyUSB0')
def main(uart):
    try:
        asyncio.run(amain(uart))
    except KeyboardInterrupt:
        pass
