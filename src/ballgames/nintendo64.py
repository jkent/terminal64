#!/usr/bin/env python3

import struct
import time

from .summercart64 import SummerCart64Protocol as Protocol

COMM_USER_DATA_TYPE = 0xFF

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
                self._flush()
                while True:
                    time.sleep(1 / 60)
                    self.loop()
                    self._flush()
                    self.frame += 1
            except KeyboardInterrupt:
                self.reset()
                self._flush()
                time.sleep(0.25)
                self.protocol.reset()

    def send_usb_packet(self, data, type=COMM_USER_DATA_TYPE):
        self.protocol.send_raw_packet('U', type, data=data)

    def on_usb_packet(self, data, type):
        if type == 5:
            self.protocol.reset()
            self.frame = 0
            self.setup()
        elif type == COMM_USER_DATA_TYPE:
            while data:
                length, type = struct.unpack_from('>HH', data)
                self.on_packet(type, data[4:4 + length])
                data = data[4 + length:]
        else:
            print(type, data)
