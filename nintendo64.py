#!/usr/bin/env python3

import struct
import time

from summercart64 import SummerCart64Protocol as Protocol


class Nintendo64:
    def __init__(self, port):
        self.port = port

    def run(self):
        with Protocol.thread_factory(self.port) as protocol:
            protocol.n64 = self
            self.protocol = protocol
            try:
                self.frame = 0
                self.setup()
                while True:
                    self.loop()
                    time.sleep(1/60)
                    self.frame += 1
            except KeyboardInterrupt:
                self.protocol.reset()

    def send_usb_packet(self, data, type=0xFF):
        self.protocol.send_raw_packet('U', type, data=data)

    def recv_usb_packet(self, data, type):
        if type == 5:
            self.frame = 0
            self.setup()
        elif type == 255:
            while data:
                length, type = struct.unpack_from('>HH', data)
                self.recv_user_pkt(type, data[4:4 + length])
                data = data[4 + length:]
        else:
            print(type, data)

    def recv_user_pkt(self, type, data):
        if type == 0:
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
