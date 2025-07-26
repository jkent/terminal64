#!/usr/bin/env python

import asyncio
from copy import deepcopy

import click

from terminal64.game.entity import CIRCLE_ENTITY, SKIP_ENTITY, TEXT_ENTITY

from .cart import SummerCart64
from .game import *
from .util import clamp


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
        self.x = disp_width / 2 - len(self.string) * 6 / 2

class Pong(Game, GameClient):
    def __init__(self, cart):
        Game.__init__(self, cart)
        GameClient.__init__(self)

    def connection_lost(self, exc):
        exit_event.set()

    def connection_made(self, transport):
        super().connection_made(transport)
        self.write_line('!join pong')

    def setup(self):
        self.score = Score()
        self.ball = Ball(4)
        self.paddle = [
            Paddle(0),
            Paddle(1)
        ]

        self.text = [
            TextEntity('Press start!'),
            TextEntity('Player 2 not ready.'),
        ]
        self.text[0].x = disp_width / 2 - len(self.text[0].string) * 6 / 2
        self.text[0].y = disp_height / 2 - 4
        self.text[1].x = disp_width / 2 - len(self.text[1].string) * 6 / 2
        self.text[1].y = disp_height / 2 + 8

        self.reset()
        self.entities = [self.score, self.ball] + self.paddle + self.text
        self.ready()

    def loop(self):
        if self.player_id is None:
            return

        self_ready = self.state['player'][self.player_id]['ready']
        other_ready = self.state['player'][1 - self.player_id]['ready']

        self.text[0].type = SKIP_ENTITY if self_ready else TEXT_ENTITY
        self.text[1].type = SKIP_ENTITY if other_ready else TEXT_ENTITY

        self.ball.x = self.state['ball']['x']
        self.ball.y = self.state['ball']['y']
        self.paddle[0].pos = self.state['paddle'][self.player_id]['pos']
        self.paddle[1].pos = self.state['paddle'][1 - self.player_id]['pos']

        # flip the field
        if self.player_id == 1:
            self.ball.x = disp_width - self.ball.x - self.ball.diameter
            self.ball.y = disp_height - self.ball.y - self.ball.diameter
            self.paddle[0].pos = -self.paddle[0].pos
            self.paddle[1].pos = -self.paddle[1].pos

        self.score.score = [
            self.state['score'][self.player_id],
            self.state['score'][1 - self.player_id]
        ]
        self.score.update()

        if not self_ready or not other_ready:
            self.ball.type = SKIP_ENTITY
        else:
            self.ball.type = CIRCLE_ENTITY

    def handle_input(self, inputs):
        super().handle_input(inputs)

        if self.player_id is None:
            return

        player = self.state['player'][self.player_id]

        if not self.last_inputs.start and inputs.start:
            player['ready'] = not player['ready']

        player['pos'] = clamp(inputs.stick_y / -72.0, -1.0, 1.0)

        self.last_inputs = deepcopy(inputs)
        self.send_delta()

async def amain(uart, host, port):
    global exit_event

    loop = asyncio.get_event_loop()
    exit_event = asyncio.Event()

    cart = await SummerCart64.connect(uart)
    _, game = await loop.create_connection(lambda: Pong(cart), host, port)
    asyncio.create_task(game.run())
    await exit_event.wait()
    game.transport.close()

@click.command
@click.argument('uart', default='/dev/ttyUSB0')
@click.argument('host', default='game.jkent.net')
@click.argument('port', default=7890)
def main(uart, host, port):
    try:
        asyncio.run(amain(uart, host, port))
    except KeyboardInterrupt:
        pass
