import asyncio
import json
import os
from copy import deepcopy

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "True"

import click
import json_delta
import pygame

MOVE_PERCENT = 0.05
DISP_WIDTH = 320
DISP_HEIGHT = 240

player_id = 0

class GameClient(asyncio.Protocol):
    def __init__(self):
        self._buffer = bytearray()
        self.state = {}
        self._last_state = deepcopy(self.state)

    def connection_made(self, transport):
        self._transport = transport
        self.write_line('!join pong')

    def connection_lost(self, exc):
        global exit_event

        exit_event.set()

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

    def line_received(self, line):
        global player_id

        args = line.split()
        cmd = args[0]

        self._last_state = deepcopy(self.state)
        if cmd == 'state':
            _, player_id, data = line.split(None, 2)
            player_id = int(player_id)
            self.state = json.loads(data)
        elif cmd == 'delta':
            _, data = line.split(None, 1)
            data = json.loads(data)
            self.state = json_delta.patch(self.state, data, False)
            self._last_state = deepcopy(self.state)
        else:
            print("unknown command???")

    def send_delta(self):
        if self.state != self._last_state:
            player = self.state['player'][player_id]
            delta = json_delta.diff(self._last_state['player'][player_id],
                                    player, verbose=False)
            data = json.dumps(delta, separators=(',', ':'))
            self.write_line(f'delta {data}')
            self._last_state['player'][player_id] = deepcopy(player)

class Paddle:
    def __init__(self, paddle_num):
        self._paddle_num = paddle_num
        self.pos = 0
        self.width = 5
        self.offset = 10
        self.size = 0.25
        if self._paddle_num == 0:
            self.x = self.offset
        elif self._paddle_num == 1:
            self.x = DISP_WIDTH - self.width - self.offset
        self.update()

    def update(self):
        self.height = DISP_HEIGHT * self.size
        self.y = (self.pos + 1) / 2 * (DISP_HEIGHT - self.height)
        self._rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        pygame.draw.rect(screen, 'white', self._rect)

class Ball:
    def __init__(self):
        self.radius = 4
        self.x = DISP_WIDTH / 2
        self.y = DISP_HEIGHT / 2
        self.update()

    def update(self):
        self._coord = pygame.Vector2(self.x + self.radius, self.y + self.radius)

    def draw(self, screen):
        pygame.draw.circle(screen, 'red', self._coord, self.radius)

class Scene:
    def __init__(self):
        self.paddle = [Paddle(n) for n in range(2)]
        self.ball = Ball()
        self.score = [0, 0]
        self.self_ready = False
        self.other_ready = False

    def update(self, client):
        if not client.state:
            return

        players = client.state.get('player')
        if players:
            player = players[player_id]
            self.self_ready = player['ready']
            player = players[1 - player_id]
            self.other_ready = player['ready']

        paddles = client.state.get('paddle')
        if paddles:
            paddle = paddles[player_id]
            self.paddle[0].pos = paddle.get('pos', 0)
            paddle = paddles[1 - player_id]
            self.paddle[1].pos = paddle.get('pos', 0)

        ball = client.state.get('ball')
        if ball:
            self.ball.x = ball['x']
            self.ball.y = ball['y']

        if player_id == 1:
            self.paddle[0].pos = -self.paddle[0].pos
            self.paddle[1].pos = -self.paddle[1].pos
            self.ball.x = 320 - self.ball.x - self.ball.radius * 2
            self.ball.y = 240 - self.ball.y - self.ball.radius * 2

        score = client.state.get('score', [0, 0])
        self.score = [score[player_id], score[1 - player_id]]

        self.paddle[0].update()
        self.paddle[1].update()
        self.ball.update()

    def draw(self, screen):
        screen.fill('black')

        font = pygame.font.SysFont('monospace', 12)
        surface = font.render(f'{self.score[0]}:{self.score[1]}', False, 'yellow')
        x = DISP_WIDTH / 2 - surface.get_width() / 2
        y = 32 / 2 - surface.get_height() / 2
        screen.blit(surface, (x, y))

        self.paddle[0].draw(screen)
        self.paddle[1].draw(screen)

        if self.self_ready and self.other_ready:
            self.ball.draw(screen)

        if not self.self_ready:
            surface = font.render('Press spacebar!', False, 'white')
            x = DISP_WIDTH / 2 - surface.get_width() / 2
            y = DISP_HEIGHT / 2 - surface.get_height() / 2 - 8
            screen.blit(surface, (x, y))

        if not self.other_ready:
            surface = font.render('Player 2: Not ready', False, 'white')
            x = DISP_WIDTH / 2 - surface.get_width() / 2
            y = DISP_HEIGHT / 2 - surface.get_height() / 2 + 8
            screen.blit(surface, (x, y))

async def event_process(events, client):
    if 'player' in client.state:
        player = client.state['player'][player_id]
    else:
        player = [None, None]
    for event in events:
        if event.type == pygame.QUIT:
            exit_event.set()

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                player['ready'] = not player['ready']
                client.send_delta()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                player['pos'] = max(-1, player['pos'] - MOVE_PERCENT)
                client.send_delta()
            if event.key == pygame.K_s:
                player['pos'] = min(1, player['pos'] + MOVE_PERCENT)
                client.send_delta()

async def async_main(host, port):
    global exit_event

    loop = asyncio.get_event_loop()
    exit_event = asyncio.Event()

    pygame.init()
    pygame.font.init()
    pygame.key.set_repeat(25, 25)

    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((DISP_WIDTH, DISP_HEIGHT))

    scene = Scene()
    transport, client = await loop.create_connection(GameClient, host, port)

    while not exit_event.is_set():
        await loop.run_in_executor(None, clock.tick, 60)
        asyncio.create_task(event_process(pygame.event.get(), client))
        await loop.run_in_executor(None, scene.update, client)
        await loop.run_in_executor(None, scene.draw, screen)
        await loop.run_in_executor(None, pygame.display.flip)
        await asyncio.sleep(0)

    transport.close()

    pygame.quit()

@click.command
@click.argument('host', default='game.jkent.net')
@click.argument('port', default=7890)
def main(host, port):
    try:
        asyncio.run(async_main(host, port))
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
