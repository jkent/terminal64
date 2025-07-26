import asyncio
import json
from copy import deepcopy

from json_delta import diff, patch

from ..game import disp_height, disp_width


class GameFullException(Exception):
    pass

class InvalidMessage(Exception):
    pass

class ServerGame:
    instances = []

    def __init__(self):
        self.player = {}
        self.state = {}
        self.last_state = {}
        loop = asyncio.get_event_loop()
        loop.create_task(self._loop())

    async def _loop(self):
        self.instances.append(self)
        self.setup()
        self.shutdown = False
        while not self.shutdown:
            if self.state != self.last_state:
                delta = diff(self.last_state, self.state, verbose=False)
                data = json.dumps(delta, separators=(',', ':'))
                for player in self.player.values():
                    player.write_line(f'delta {data}')
                self.last_state = deepcopy(self.state)
            await asyncio.sleep(1/60)
            self.loop()
        self.instances.remove(self)

    def _join(self, client):
        for player_id in range(self.max_players):
            if player_id not in self.player:
                self.player[player_id] = client
                client.player_id = player_id
                break
        else:
            raise GameFullException

        self.join(client.player_id)

        data = json.dumps(self.state, separators=(',', ':'))
        client.write_line(f'state {client.player_id} {data}')

    def _leave(self, client):
        try:
            del self.player[client.player_id]
        except ValueError:
            return

        self.leave(client.player_id)

        if len(self.player) == 0:
            self.shutdown = True

    def _patch(self, client, diff):
        before = self.state['player'][client.player_id]
        after = patch(before, diff, False)
        self.state['player'][client.player_id] = after
        self.patch(before, after)

    def setup(self):
        pass

    def loop(self):
        pass

    def join(self, player_id):
        pass

    def leave(self, player_id):
        pass

    def patch(self, before, after):
        pass

class GameProtocol(asyncio.Protocol):
    games = {}

    def __init__(self):
        self._buffer = bytearray()
        self._game = None
        self._transport = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print(f'Connection from: {peername}')
        self._transport = transport

    def connection_lost(self, exc):
        peername = self._transport.get_extra_info('peername')
        print(f'Connection lost: {peername}')
        if self._game is not None:
            self._game._leave(self)
            self._game = None

    def data_received(self, data):
        self._buffer.extend(data)
        self._process_buffer()

    def _process_buffer(self):
        while True:
            newline_index = self._buffer.find(b'\n')
            if newline_index == -1:
                break

            line = self._buffer[:newline_index + 1]
            del self._buffer[:newline_index + 1]

            self.line_received(line.decode().strip())

    def write_line(self, line):
        self._transport.write(f'{line}\n'.encode())

    def line_received(self, line: str):
        args = line.split()
        cmd = args[0]

        if cmd.startswith('!'):
            if cmd == '!join' and len(args) == 2:
                self._join(args[1])
            elif cmd == '!leave' and len(args) == 1:
                self._leave()
            elif cmd == '!close' and len(args) == 1:
                if self._game is not None:
                    self._leave()
                self._transport.close()
            else:
                self.write_line('error \'invalid server command\'')
                return
        elif self._game is not None:
            if cmd == 'delta':
                _, data = line.split(None, 1)
                try:
                    diff = json.loads(data)
                    self._game._patch(self, diff)
                except:
                    raise InvalidMessage
            else:
                raise InvalidMessage
        else:
            self.write_line('error \'not in a game\'')
            return

    def _join(self, name):
        if self._game is not None:
            self.write_line('error \'already in a game\'')
            return

        if name not in GameProtocol.games:
            self.write_line('error \'invalid game name\'')
            return

        for instance in GameProtocol.games[name].instances:
            try:
                instance._join(self)
                self._game = instance
                return
            except GameFullException:
                pass

        instance = GameProtocol.games[name]()
        instance._join(self)
        self._game = instance

    def _leave(self):
        if self._game is None:
            self.write_line('error \'not in a game\'')
            return

        self._game._leave(self)
        self._game = None

async def async_main():
    loop = asyncio.get_event_loop()
    server = await loop.create_server(GameProtocol, '0.0.0.0', 7890)

    for socket in server.sockets:
        print(f'Server listening: {socket.getsockname()}')

    async with server:
        await server.serve_forever()

def main():
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        pass

from .pong import PongGame

GameProtocol.games['pong'] = PongGame
