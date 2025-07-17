#!/usr/bin/env python

import random
import sys

from entity import Entity
from game import Game

display_width = 320
display_height = 240

def clamp(value, min_, max_):
    return min(max_, max(min_, value))

class Paddle(Entity):
    paddle_id_next = 0

    def __init__(self):
        super().__init__(type='rect')
        self.paddle_id = Paddle.paddle_id_next
        Paddle.paddle_id_next += 1
        self.color.tuple = (0xFF, 0xFF, 0xFF, 0xFF)
        offset = 10
        self.rect.width = 5
        if self.paddle_id == 0:
            self.rect.x = offset
        elif self.paddle_id == 1:
            self.rect.x = display_width - self.rect.width - offset
        self.size = 0.25

    @property
    def pos(self):
        return self.rect.y * 2 / (display_height - self.rect.height) - 1
    @pos.setter
    def pos(self, value):
        self.rect.y = (value + 1) / 2 * (display_height - self.rect.height)

    @property
    def size(self):
        return display_height / self.rect.height
    @pos.setter
    def size(self, value):
        self.rect.height = display_height * value

class Ball(Entity):
    def __init__(self, radius):
        super().__init__(type='ball')
        self.color.tuple = (0xFF, 0x00, 0x00, 0xFF)
        self.radius = radius

    @property
    def radius(self):
        return self.rect.height
    @radius.setter
    def radius(self, value):
        self.rect.height = value

class Score(Entity):
    def __init__(self):
        super().__init__(type='text')
        self.color.tuple = (0xFF, 0xFF, 0xFF, 0xFF)
        self.reset()

    def reset(self):
        self.score = [0, 0]
        self.update()

    def increment(self, player):
        self.score[player] += 1
        self.update()

    def update(self):
        self.text = f'{self.score[0]}:{self.score[1]}'
        self.rect.tuple = (320 / 2 - len(self.text) * 8 / 2, 16, 0, 0)

class Pong(Game):
    paddle_size = 0.25

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paddle = (Paddle(), Paddle())
        self.ball = Ball(7)
        self.score = Score()
        self.entities = self.paddle + (self.ball, self.score)

    def setup(self):
        for entity in self.entities:
            entity._dirty = True
        for paddle in self.paddle:
            paddle.pos = 0
        self.score.reset()
        self.reset()
        self.write_ready()
        self.flush_user()

    def loop(self):
        self.ball.rect.x = clamp(self.ball.rect.x + self.delta_x, 0, display_width - 1)
        self.ball.rect.y = clamp(self.ball.rect.y + self.delta_y, 0, display_height - 1)

        if self.check_collision(self.ball, self.paddle[0]):
            self.delta_x = 3
        elif self.check_collision(self.ball, self.paddle[1]):
            self.delta_x = -3
        elif self.ball.rect.y == 0 or self.ball.rect.y == display_height - 1:
            self.delta_y = -self.delta_y

        if self.ball.rect.x == 0:
            self.score.increment(1)
            self.reset(1)
        elif self.ball.rect.x == display_width - 1:
            self.score.increment(0)
            self.reset(0)

        self.write_entities()
        self.flush_user()

    def inputs_change(self, inputs):
        pos = clamp(inputs['stick_y'] / -72.0, -1.0, 1.0)
        self.paddle[0].pos = pos
        self.paddle[1].pos = -pos

    def reset(self, winner=1):
        self.ball.rect.x = display_width / 2 - self.ball.radius / 2
        self.ball.rect.y = display_height / 2 - self.ball.radius / 2
        self.delta_x = -3 if winner == 0 else 3
        self.delta_y = random.choice([-3, 3])

if __name__ == '__main__':
    try:
        port = sys.argv[1]
    except:
        port = '/dev/ttyUSB0'

    pong = Pong(port)
    pong.run()
