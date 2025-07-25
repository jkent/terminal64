import random

from ..game import (CircleEntity, RectangleEntity, collision, disp_height,
                    disp_width)
from ..util import clamp
from . import ServerGame


class Paddle(RectangleEntity):
    def __init__(self, player):
        super().__init__()
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
        return self.height / disp_height
    @size.setter
    def size(self, value):
        self.height = disp_height * value

    @property
    def state(self):
        return {
            'size': self.size,
            'pos': self.pos,
        }

class Ball(CircleEntity):
    def __init__(self, radius):
        super().__init__()
        self.radius = radius

    @property
    def delta_x(self):
        return self._delta_x
    @delta_x.setter
    def delta_x(self, value):
        self._delta_x = value

    @property
    def delta_y(self):
        return self._delta_y
    @delta_y.setter
    def delta_y(self, value):
        self._delta_y = value

    @property
    def state(self):
        return {
            'radius': self.radius,
            'x': self.x,
            'y': self.y,
        }

    def move(self):
        self.x += self.delta_x
        self.y += self.delta_y

class PongGame(ServerGame):
    max_players = 2

    def __init__(self):
        super().__init__()
        self.state = {
            'player': [
                {'ready': None, 'pos': 0},
                {'ready': None, 'pos': 0},
            ],
        }

    def setup(self):
        self.ball = Ball(4)
        self.paddle = [Paddle(0), Paddle(1)]
        self.reset()

    def reset(self, winner=None):
        self.ball.x = disp_width / 2
        self.ball.y = disp_height / 2
        self.ball.delta_x = -3 if winner else 3
        self.ball.delta_y = random.choice([-3, 3])

        for player in self.state['player']:
            if player['ready']:
                player['ready'] = False

        if winner is None:
            self.state['score'] = [0, 0]
        self.state['ball'] = self.ball.state
        self.state['paddle'] = [self.paddle[0].state, self.paddle[1].state]

    def loop(self):
        ready = 0
        for player in self.state['player']:
            if player['ready']:
                ready += 1

        pos = self.state['player'][0].setdefault('pos', 0)
        self.paddle[0].pos = clamp(pos, -1, 1)
        pos = -self.state['player'][1].setdefault('pos', 0)
        self.paddle[1].pos = clamp(pos, -1, 1)

        self.state['paddle'] = [self.paddle[0].state, self.paddle[1].state]
        if ready < 2:
            return

        self.ball.move()

        if self.ball.y == self.ball.min_y or self.ball.y == self.ball.max_y:
            self.ball.delta_y = -self.ball.delta_y

        if collision(self.ball, self.paddle[0]):
            self.ball.delta_x = abs(self.ball.delta_x)
        elif collision(self.ball, self.paddle[1]):
            self.ball.delta_x = -abs(self.ball.delta_x)
        elif self.ball.x == self.ball.min_x:
            self.state['score'][1] += 1
            self.reset(winner=0)
        elif self.ball.x == self.ball.max_x:
            self.state['score'][0] += 1
            self.reset(winner=1)

        self.state['ball'] = self.ball.state

    def join(self, player_id):
        self.state['player'][player_id]['ready'] = False

    def leave(self, player_id):
        self.state['score'][player_id] = 0
        self.state['player'][player_id] = {
            'ready': None,
            'pos': 0,
        }
