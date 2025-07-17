#!/usr/bin/env python

import random
import sys

from game import Entity, Game, collision

display_width = 320
display_height = 240

def clamp(value, min_, max_):
    return min(max_, max(min_, value))

class Paddle(Entity):
    def __init__(self, id):
        super().__init__()
        self.type = 'rectangle'
        self.color = (0xFF, 0xFF, 0xFF)
        self.size = 0.25
        self.width = 5
        offset = 10
        if id == 0:
            self.x = offset
        elif id == 1:
            self.x = display_width - self.width - offset

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

class Ball(Entity):
    def __init__(self, radius):
        super().__init__()
        self.type = 'circle'
        self.color = (0xFF, 0x00, 0x00)
        self.radius = radius

class Score(Entity):
    def __init__(self):
        super().__init__()
        self.type = 'text'
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
        self.text = f'{self.score[0]}:{self.score[1]}'
        self.x = 320 / 2 - len(self.text) * 8 / 2

class Pong(Game):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paddles = [Paddle(0), Paddle(1)]
        self.ball = Ball(4)
        self.score = Score()
        self.entities = [self.score, self.ball] + self.paddles

    def setup(self):
        for entity in self.entities:
            entity._dirty = True
        for paddle in self.paddles:
            paddle.pos = 0
        self.score.reset()
        self.reset()
        self._ready()
        self.flush()

    def loop(self):
        self.ball.x = clamp(self.ball.x + self.delta_x, 0, display_width - 1)
        self.ball.y = clamp(self.ball.y + self.delta_y, 0, display_height - 1)

        if collision(self.ball.bbox, self.paddles[0].bbox):
            self.delta_x = 3
        elif collision(self.ball.bbox, self.paddles[1].bbox):
            self.delta_x = -3
        elif self.ball.y == 0 or self.ball.y == display_height - 1:
            self.delta_y = -self.delta_y

        if self.ball.x == 0:
            self.score.increment(1)
            self.reset(1)
        elif self.ball.x == display_width - 1:
            self.score.increment(0)
            self.reset(0)

        self.flush()

    def on_inputs(self, inputs):
        pos = clamp(inputs['stick_y'] / -72.0, -1.0, 1.0)
        self.paddles[0].pos = pos
        self.paddles[1].pos = -pos

    def reset(self, winner=1):
        self.ball.x = display_width / 2 - self.ball.radius / 2
        self.ball.y = display_height / 2 - self.ball.radius / 2
        self.delta_x = -3 if winner == 0 else 3
        self.delta_y = random.choice([-3, 3])

if __name__ == '__main__':
    try:
        port = sys.argv[1]
    except:
        port = '/dev/ttyUSB0'

    pong = Pong(port)
    pong.run()
