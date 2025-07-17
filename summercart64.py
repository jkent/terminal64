import time
from struct import Struct

import serial.threaded
from serial import Serial

request_struct = Struct('>3sBII')
response_struct = Struct('>3sBI')

class SummerCart64Protocol(serial.threaded.Protocol):
    def __init__(self):
        super().__init__()
        self._recvbuf = b''

    def connection_made(self, transport):
        self.transport = transport
        self.reset()

    def reset(self):
        count = 0
        self.transport.serial.dtr = True
        while not self.transport.serial.dsr and count < 10:
            time.sleep(0.01)
            count += 1

        count = 0
        self.transport.serial.dtr = False
        while self.transport.serial.dsr and count < 10:
            time.sleep(0.01)
            count += 1

    def data_received(self, data):
        self._recvbuf += data
        while True:
            if len(self._recvbuf) < 8:
                break

            if self._recvbuf[0:3] not in (b'CMP', b'ERR', b'PKT'):
                self.reset()

            packet = self.recv_raw_packet()
            if not packet:
                return

            if packet[0] == 'PKT' and packet[1] == 'U':
                info = int.from_bytes(packet[3][:4], 'big')
                type, length = info >> 24, info & 0xffffff
                self.n64.recv_usb_packet(packet[3][4:4 + length], type)
            else:
                print(packet)

    def recv_raw_packet(self):
        pkt_type, pkt_id, length = response_struct.unpack_from(self._recvbuf)
        pkt_len = response_struct.size + length
        if len(self._recvbuf) >= pkt_len:
            data = self._recvbuf[response_struct.size:pkt_len]
            self._recvbuf = self._recvbuf[pkt_len:]
            return pkt_type.decode(), chr(pkt_id), length, data

    def send_raw_packet(self, pkt_id, arg0=0, arg1=0, data=b''):
        if pkt_id in 'MU':
            arg1 = len(data)
        if not isinstance(pkt_id, int):
            pkt_id = ord(pkt_id)
        buf = request_struct.pack(b'CMD', pkt_id, arg0, arg1) + data
        self.transport.write(buf)

    @classmethod
    def thread_factory(cls, port):
        return serial.threaded.ReaderThread(Serial(port), cls)
