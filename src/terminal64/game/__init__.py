import asyncio
from copy import deepcopy
import json

import json_delta

from .. import USB_HEARTBEAT, Terminal64
from .display import disp_height, disp_width
from .entity import (CircleEntity, Entity, RectangleEntity, SpriteEntity,
                     TextEntity)
from .sprite import Sprite
from .util import collision, decode_input

__all__ = ['CircleEntity', 'Entity', 'Game', 'GameClient', 'RectangleEntity',
           'Sprite', 'SpriteEntity', 'TextEntity', 'collision', 'disp_height',
           'disp_width']

GAME_IN_INPUT       = 0

GAME_OUT_RESET      = 0
GAME_OUT_READY      = 1
GAME_OUT_BGCOLOR    = 2
GAME_OUT_SPRITE     = 3
GAME_OUT_ENTITY     = 4

class Game:
    def __init__(self, cart):
        self.t64 = Terminal64(cart)
        self.t64.usb_pkt_handlers[USB_HEARTBEAT] = self.handle_usb_heartbeat
        self.t64.handle_usb_message = self.handle_usb_message
        self.reset()

    def handle_usb_heartbeat(self, data):
        asyncio.create_task(self.areset())

    def handle_usb_message(self, message_type, data):
        if message_type == GAME_IN_INPUT:
            input = decode_input(data)
            self.handle_input(input)
        else:
            print('unhandled message:', message_type, data)

    def reset(self):
        self.frame = 0
        self.sprites = []
        self.entities = []
        self.t64.queue_usb_message(GAME_OUT_RESET)

    async def areset(self):
        await self.t64.cartridge.resync()
        self.reset()
        self.setup()
        self.flush()

    def ready(self):
        self.t64.queue_usb_message(GAME_OUT_READY)

    def flush(self):
        for i, sprite in enumerate(self.sprites):
            if sprite.dirty:
                self.t64.queue_usb_message(GAME_OUT_SPRITE, sprite.message(i))
        for i, entity in enumerate(self.entities):
            if entity.dirty:
                self.t64.queue_usb_message(GAME_OUT_ENTITY, entity.message(i))
        self.t64.send_usb_messages()

    async def run(self):
        try:
            self.reset()
            self.setup()
            self.flush()
            while True:
                await asyncio.sleep(1/60)
                self.loop()
                self.flush()
                self.frame += 1
        except asyncio.CancelledError:
            self.reset()
            self.flush()

    """User function expected to be overridden"""
    def setup(self):
        pass

    """User function expected to be overridden"""
    def loop(self):
        pass

    """User function expected to be inherited"""
    def handle_input(self, input):
        if not hasattr(self, 'last_inputs'):
            self.last_inputs = decode_input(b'\0\0\0\0\0\0\0\0')

class GameClient(asyncio.Protocol):
    def __init__(self):
        self.client_buffer = bytearray()
        self.state = {}
        self._state_last = deepcopy(self.state)
        self.player_id = None

    def connection_made(self, transport):
        self.transport = transport
        self.player_id = None

    def data_received(self, data):
        self.client_buffer.extend(data)
        while True:
            newline_index = self.client_buffer.find(b'\n')
            if newline_index == -1:
                break

            line = self.client_buffer[:newline_index + 1]
            del self.client_buffer[:newline_index + 1]

            self.line_received(line.decode().strip())

    def write_line(self, line):
        self.transport.write(f'{line}\n'.encode())

    def line_received(self, line):
        args = line.split()
        cmd = args[0]

        if cmd == 'state':
            _, player_id, data = line.split(None, 2)
            self.player_id = int(player_id)
            self.state = json.loads(data)
        elif cmd == 'delta':
            _, data = line.split(None, 1)
            data = json.loads(data)
            self.state = json_delta.patch(self.state, data, False)
        else:
            print(f'Unknown command `{cmd}`???')
        self._state_last = deepcopy(self.state)

    def send_delta(self):
        if self.player_id == None:
            return

        player = self.state['player'][self.player_id]
        if player != self._state_last['player'][self.player_id]:
            delta = json_delta.diff(self._state_last['player'][self.player_id],
                                    player, verbose=False)
            data = json.dumps(delta, separators=(',', ':'))
            self.write_line(f'delta {data}')
            self._state_last['player'][self.player_id] = deepcopy(player)
