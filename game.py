import struct
from types import SimpleNamespace

from nintendo64 import Nintendo64


GAME_IN_INPUT = 0

GAME_OUT_RESET   = 0
GAME_OUT_READY   = 1
GAME_OUT_BGCOLOR = 2
GAME_OUT_SPRITE  = 3
GAME_OUT_ENTITY  = 4

def collision(a, b):
    return a.x0 <= b.x1 and a.x1 >= b.x0 and a.y0 <= b.y1 and a.y1 >= b.y0

class Game(Nintendo64):
    def __init__(self, port):
        super().__init__(port)
        self._send_buf = b''
        self.sprites = []
        self.entities = []

    def on_packet(self, type, data):
        if type == GAME_IN_INPUT:
            btn, stick_x, stick_y, cstick_x, cstick_y, analog_l, analog_r = \
                struct.unpack('>Hbbbbbb', data)
            inputs = SimpleNamespace(
                a = bool(btn & (1 << 15)),
                b = bool(btn & (1 << 14)),
                z = bool(btn & (1 << 13)),
                start = bool(btn & (1 << 12)),
                d_up = bool(btn & (1 << 11)),
                d_down = bool(btn & (1 << 10)),
                d_left = bool(btn & (1 << 9)),
                d_right = bool(btn & (1 << 8)),
                y = bool(btn & (1 << 7)),
                x = bool(btn & (1 << 6)),
                l = bool(btn & (1 << 5)),
                r = bool(btn & (1 << 4)),
                c_up = bool(btn & (1 << 3)),
                c_down = bool(btn & (1 << 2)),
                c_left = bool(btn & (1 << 1)),
                c_right = bool(btn & (1 << 0)),
                stick_x = stick_x,
                stick_y = stick_y,
                cstick_x = cstick_x,
                cstick_y = cstick_y,
                analog_l = analog_l,
                analog_r = analog_r,
            )
            self.on_input(inputs)
        else:
            print(type, data)

    def reset(self):
        self.sprites = []
        self.entities = []
        self._send_buf += struct.pack('>HH', 0, GAME_OUT_RESET)

    def ready(self):
        self._send_buf += struct.pack('>HH', 0, GAME_OUT_READY)

    def _flush(self, reset=False):
        for i, sprite in enumerate(self.sprites):
            if sprite.dirty:
                pkt = i.to_bytes(2) + sprite.raw
                data = struct.pack('>HH', len(pkt), GAME_OUT_SPRITE) + pkt
                self._send_buf += data
        for i, entity in enumerate(self.entities):
            if entity.dirty:
                pkt = i.to_bytes(2) + entity.raw
                data = struct.pack('>HH', len(pkt), GAME_OUT_ENTITY) + pkt
                self._send_buf += data
        if self._send_buf:
            self.send_usb_packet(self._send_buf)
            self._send_buf = b''

    # User functions to be overridden
    def setup(self):
        pass

    def loop(self):
        pass

    def on_input(self, inputs):
        print(inputs)

class Sprite:
    def __init__(self):
        self._data = b''
        self._dirty = True

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        if self.data == value:
            return
        self._data = value
        self._dirty = True

    @property
    def dirty(self):
        return self._dirty

    @property
    def raw(self):
        self._dirty = False
        return self.data

    def load(self, path):
        with open(path, 'rb') as f:
            self.data = f.read()

class Entity:
    types = ['none', 'sprite', 'rectangle', 'circle', 'text']

    def __init__(self):
        self._raw = bytearray(16)
        self._raw[15] = 0xFF
        self._data = b''
        self._dirty = True

    @property
    def type(self):
        return Entity.types[self._raw[0]]
    @type.setter
    def type(self, value):
        if self.type == value:
            return
        try:
            self._raw[0] = Entity.types.index(value)
        except:
            self._raw[0] = 0
        self._dirty = True

    @property
    def flags(self):
        return self._raw[1]
    @flags.setter
    def flags(self, value):
        if self.flags == value:
            return
        self._raw[1] = value
        self._dirty = True

    @property
    def idx(self):
        return int.from_bytes(self._raw[2:4])
    @idx.setter
    def idx(self, value):
        if self.idx == value:
            return
        self._raw[2:4] = value.to_bytes(2)
        self._dirty = True

    @property
    def x(self):
        return int.from_bytes(self._raw[4:6])
    @x.setter
    def x(self, value):
        value = int(value)
        if self.x == value:
            return
        self._raw[4:6] = value.to_bytes(2)
        self._dirty = True

    @property
    def y(self):
        return int.from_bytes(self._raw[6:8])
    @y.setter
    def y(self, value):
        value = int(value)
        if self.y == value:
            return
        self._raw[6:8] = value.to_bytes(2)
        self._dirty = True

    @property
    def width(self):
        return int.from_bytes(self._raw[8:10])
    @width.setter
    def width(self, value):
        value = int(value)
        if self.width == value:
            return
        self._raw[8:10] = value.to_bytes(2)
        self._dirty = True

    @property
    def radius(self):
        return int.from_bytes(self._raw[8:10])
    @radius.setter
    def radius(self, value):
        if self.radius == value:
            return
        self._raw[8:10] = value.to_bytes(2)
        self._dirty = True

    @property
    def stride(self):
        return int.from_bytes(self._raw[8:10])
    @stride.setter
    def stride(self, value):
        if self.stride == value:
            return
        self._raw[8:10] = value.to_bytes(2)
        self._dirty = True

    @property
    def height(self):
        return int.from_bytes(self._raw[10:12])
    @height.setter
    def height(self, value):
        value = int(value)
        if self.height == value:
            return
        self._raw[10:12] = value.to_bytes(2)
        self._dirty = True

    @property
    def bbox(self):
        return SimpleNamespace(x0 = self.x, y0 = self.y,
                               x1 = self.x + self.width,
                               y1 = self.y + self.height)

    @property
    def color(self):
        r = self._raw[12]
        g = self._raw[13]
        b = self._raw[14]
        a = self._raw[15]
        return (r,g,b,a)
    @color.setter
    def color(self, value):
        if len(value) == 3:
            value = value + (0xFF,)
        if self.color == value:
            return
        self._raw[12] = value[0]
        self._raw[13] = value[1]
        self._raw[14] = value[2]
        self._raw[15] = value[3]
        self._dirty = True

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        if self.data == value:
            return
        self._data = value
        self._dirty = True

    @property
    def text(self):
        return self.data[:-1].decode()
    @text.setter
    def text(self, value):
        self.data = value.encode() + b'\0'

    @property
    def dirty(self):
        return self._dirty

    @property
    def raw(self):
        self._dirty = False
        return self._raw + self.data
