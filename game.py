import struct
import time

from nintendo64 import Nintendo64


GAME_IN_INPUT = 0

GAME_OUT_RESET  = 0
GAME_OUT_READY  = 1
GAME_OUT_ENTITY = 2

class Game(Nintendo64):
    def __init__(self, port):
        super().__init__(port)
        self.entities = []
        self.user_send_buf = b''

    def recv_user_pkt(self, type, data):
        if type == GAME_IN_INPUT:
            btn, stick_x, stick_y, cstick_x, cstick_y, analog_l, analog_r = \
                struct.unpack('>Hbbbbbb', data)
            inputs = {
                'a': bool(btn & (1 << 15)),
                'b': bool(btn & (1 << 14)),
                'z': bool(btn & (1 << 13)),
                'start': bool(btn & (1 << 12)),
                'd_up': bool(btn & (1 << 11)),
                'd_down': bool(btn & (1 << 10)),
                'd_left': bool(btn & (1 << 9)),
                'd_right': bool(btn & (1 << 8)),
                'y': bool(btn & (1 << 7)),
                'x': bool(btn & (1 << 6)),
                'l': bool(btn & (1 << 5)),
                'r': bool(btn & (1 << 4)),
                'c_up': bool(btn & (1 << 3)),
                'c_down': bool(btn & (1 << 2)),
                'c_left': bool(btn & (1 << 1)),
                'c_right': bool(btn & (1 << 0)),
                'stick_x': stick_x,
                'stick_y': stick_y,
                'cstick_x': cstick_x,
                'cstick_y': cstick_y,
                'analog_l': analog_l,
                'analog_r': analog_r,
            }
            self.inputs_change(inputs)
        else:
            print(type, data)

    def inputs_change(self, inputs):
        print(inputs)

    def check_collision(self, a, b):
        a = a.rect.bbox
        b = b.rect.bbox
        return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]

    def write_reset(self):
        self.user_send_buf += struct.pack('>HH', 0, GAME_OUT_RESET)

    def write_ready(self):
        self.user_send_buf += struct.pack('>HH', 0, GAME_OUT_READY)

    def write_entities(self):
        for entity in self.entities:
            if entity.dirty:
                self.user_send_buf += entity.packet

    def flush_user(self):
        if self.user_send_buf:
            self.send_usb_packet(self.user_send_buf)
            self.user_send_buf = b''
