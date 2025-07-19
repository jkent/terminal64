#!/usr/bin/env python

import random

import click

from . import CircleEntity, Game, RectangleEntity, TextEntity, collision

display_width = 320
display_height = 240

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
            self.x = display_width - self.width - offset
        self.pos = 0

    @property
    def pos(self):
        return self.y * 2 / (display_height - self.height) - 1
    @pos.setter
    def pos(self, value):
        self.y = (value + 1) / 2 * (display_height - self.height)

    @property
    def size(self):
        return display_height / self.height
    @pos.setter
    def size(self, value):
        self.height = display_height * value

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
        self.x = display_width / 2 - len(self.string) * 8 / 2

class PongGame(Game):
    def setup(self):
        self.score = Score()
        self.ball = Ball(4)
        self.paddles = [Paddle(0), Paddle(1)]
        self.restart()

    def loop(self):
        self.ball.x = clamp(self.ball.x + self.delta_x, 0, display_width - self.ball.diameter - 1)
        self.ball.y = clamp(self.ball.y + self.delta_y, 0, display_height - self.ball.diameter- 1)

        if collision(self.ball, self.paddles[0]):
            self.delta_x = 3
        elif collision(self.ball, self.paddles[1]):
            self.delta_x = -3
        elif self.ball.y == 0 or self.ball.y == display_height - self.ball.diameter - 1:
            self.delta_y = -self.delta_y

        if self.ball.x == 0:
            self.score.increment(1)
            self.restart(1)
        elif self.ball.x == display_width - self.ball.diameter - 1:
            self.score.increment(0)
            self.restart(0)

    def on_input(self, inputs):
        pos = clamp(inputs.stick_y / -72.0, -1.0, 1.0)
        self.paddles[0].pos = pos
        self.paddles[1].pos = -pos

    def restart(self, winner=1):
        self.reset()
        self.entities = [self.score, self.ball] + self.paddles
        for entity in self.entities:
            entity._dirty = True
        self.ball.x = display_width / 2 - self.ball.radius / 2
        self.ball.y = display_height / 2 - self.ball.radius / 2
        self.delta_x = 3 if winner == 1 else -3
        self.delta_y = random.choice([3, -3])
        self.ready()

@click.command
@click.argument('port', default='/dev/ttyUSB0')
def main(port):
    PongGame(port).run()
