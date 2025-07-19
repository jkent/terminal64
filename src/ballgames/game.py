import struct
from types import SimpleNamespace

from bitstring import Bits, BitStream, ConstBitStream

from .nintendo64 import Nintendo64

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
            inputs = SimpleNamespace()

            bs = ConstBitStream(data)
            inputs.a        = bs.read(1).u
            inputs.b        = bs.read(1).u
            inputs.z        = bs.read(1).u
            inputs.start    = bs.read(1).u
            inputs.d_up     = bs.read(1).u
            inputs.d_down   = bs.read(1).u
            inputs.d_left   = bs.read(1).u
            inputs.d_right  = bs.read(1).u
            inputs.y        = bs.read(1).u
            inputs.x        = bs.read(1).u
            inputs.l        = bs.read(1).u
            inputs.r        = bs.read(1).u
            inputs.c_up     = bs.read(1).u
            inputs.c_down   = bs.read(1).u
            inputs.c_left   = bs.read(1).u
            inputs.c_right  = bs.read(1).u
            inputs.stick_x  = bs.read(8).i
            inputs.stick_y  = bs.read(8).i
            inputs.cstick_x = bs.read(8).i
            inputs.cstick_y = bs.read(8).i
            inputs.analog_l = bs.read(8).i
            inputs.analog_r = bs.read(8).i

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
                pkt = i.to_bytes(2) + sprite.data
                data = struct.pack('>HH', len(pkt), GAME_OUT_SPRITE) + pkt
                self._send_buf += data
                sprite.dirty = False
        for i, entity in enumerate(self.entities):
            if entity.dirty:
                pkt = i.to_bytes(2) + entity.data
                data = struct.pack('>HH', len(pkt), GAME_OUT_ENTITY) + pkt
                self._send_buf += data
                entity.dirty = False
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
    def __init__(self, path=None):
        self._data = b''
        self._dirty = True
        if path:
            self.load(path)

    @property
    def dirty(self):
        return self._dirty
    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    @property
    def data(self):
        return self._data

    def load(self, path):
        with open(path, 'rb') as f:
            self._data = f.read()
        self._dirty = True

class Entity:
    def __init__(self):
        self._type = 0
        self._dirty = True
        self._data = b''

    @property
    def dirty(self):
        return self._dirty
    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        return bs

    @property
    def data(self):
        return self.bitstream.bytes + self._data

class SpriteEntity(Entity):
    def __init__(self):
        super().__init__()
        self._type = 1
        self._index = 0
        self._tile = 0
        self._x = 0
        self._y = 0
        self._flags = 0
        self._cx = 0
        self._cy = 0
        self._scale_x = 0.0
        self._scale_y = 0.0
        self._theta = 0.0

    @property
    def index(self):
        return self._index
    @index.setter
    def index(self, value):
        if value != self._index:
            self._index = value
            self._dirty = True

    @property
    def tile(self):
        return self._tile
    @tile.setter
    def tile(self, value):
        if value != self._tile:
            self._tile = value
            self._dirty = True

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        if value != self._x:
            self._x = value
            self._dirty = True

    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        if value != self._y:
            self._y = value
            self._dirty = True

    @property
    def flags(self):
        return self._flags

    @property
    def flip_x(self):
        return bool(self.flags & (1 << 0))
    @flip_x.setter
    def flip_x(self, value):
        value = bool(value)
        if value != self.flip_x:
            self.flags &= ~(1 << 0)
            self.flags |= value << 0
            self._dirty = True

    @property
    def flip_y(self):
        return bool(self.flags & (1 << 1))
    @flip_y.setter
    def flip_y(self, value):
        value = bool(value)
        if value != self.flip_y:
            self.flags &= ~(1 << 1)
            self.flags |= value << 1
            self._dirty = True

    @property
    def cx(self):
        return self._cx
    @cx.setter
    def cx(self, value):
        if value != self._cx:
            self._cx = value
            self._dirty = True

    @property
    def cy(self):
        return self._cy
    @cy.setter
    def cy(self, value):
        if value != self._cy:
            self._cy = value
            self._dirty = True

    @property
    def scale_x(self):
        return self._scale_x
    @scale_x.setter
    def scale_x(self, value):
        if value != self._scale_x:
            self._scale_x = value
            self._dirty = True

    @property
    def scale_y(self):
        return self._scale_y
    @scale_y.setter
    def scale_y(self, value):
        if value != self._scale_y:
            self._scale_y = value
            self._dirty = True

    @property
    def theta(self):
        return self._theta
    @theta.setter
    def theta(self, value):
        if value != self._theta:
            self._theta = value
            self._dirty = True

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        self._width = value

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, value):
        self._height = value

    @property
    def x0(self):
        return self._x

    @property
    def y0(self):
        return self._y

    @property
    def x1(self):
        return self._x + self._width

    @property
    def y1(self):
        return self._y + self._height

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        bs.append(Bits(uint=self._index, length=8))
        bs.append(Bits(uint=self._tile, length=8))
        bs.append(Bits(float16=self._x))
        bs.append(Bits(float16=self._y))
        bs.append(Bits(uint=self._flags, length=8))
        bs.append(Bits(uint=int(self._cx), length=8))
        bs.append(Bits(uint=int(self._cy), length=8))
        bs.append(Bits(float16=self.scale_x))
        bs.append(Bits(float16=self.scale_y))
        bs.append(Bits(float16=self.theta))
        return bs

class RectangleEntity(Entity):
    def __init__(self):
        super().__init__()
        self._type = 2
        self._x0 = 0
        self._y0 = 0
        self._x1 = 0
        self._y1 = 0
        self._color = 0x0001

    @property
    def x0(self):
        return self._x0
    @x0.setter
    def x0(self, value):
        if value != self._x0:
            self._x0 = value
            self._dirty = True

    @property
    def y0(self):
        return self._y0
    @y0.setter
    def y0(self, value):
        if value != self._y0:
            self._y0 = value
            self._dirty = True

    @property
    def x1(self):
        return self._x1
    @x1.setter
    def x1(self, value):
        if value != self._x1:
            self._x1 = value
            self._dirty = True

    @property
    def y1(self):
        return self._y1
    @y1.setter
    def y1(self, value):
        if value != self._y1:
            self._y1 = value
            self._dirty = True

    @property
    def x(self):
        return self._x0
    @x.setter
    def x(self, value):
        if value != self._x0:
            delta_x = value - self._x0
            self._x0 += delta_x
            self._x1 += delta_x
            self._dirty = True

    @property
    def y(self):
        return self._y1
    @y.setter
    def y(self, value):
        if value != self._y1:
            delta_y = value - self._y0
            self._y0 += delta_y
            self._y1 += delta_y
            self._dirty = True

    @property
    def width(self):
        return self._x1 - self._x0
    @width.setter
    def width(self, value):
        if value != self.width:
            self._x1 = self._x0 + value
            self._dirty = True

    @property
    def height(self):
        return self._y1 - self._y0
    @height.setter
    def height(self, value):
        if value != self.height:
            self._y1 = self._y0 + value
            self._dirty = True

    @property
    def color(self):
        r = (self._color >> 11) & 0x1f
        g = (self._color >> 6) & 0x1f
        b = (self._color >> 1) & 0x1f
        r = ((r << 3) | (r >> 2)) & 0xff
        g = ((g << 3) | (g >> 2)) & 0xff
        b = ((b << 3) | (b >> 2)) & 0xff
        a = 0xff if (self._color & 1) else 0
        return (r, g, b, a)
    @color.setter
    def color(self, value):
        if len(value) == 3:
            value = value + (0xff,)
        if value != self.color:
            r = value[0] >> 3 & 0x1f
            g = value[1] >> 3 & 0x1f
            b = value[2] >> 3 & 0x1f
            a = value[3] >> 7 & 1
            self._color = (r << 11) | (g << 6) | (b << 1) | a
            self._dirty = True

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        bs.append(Bits(uint=int(self._x0), length=12))
        bs.append(Bits(uint=int(self._y0), length=12))
        bs.append(Bits(uint=int(self._x1), length=12))
        bs.append(Bits(uint=int(self._y1), length=12))
        bs.append(Bits(uint=self._color, length=16))
        return bs

class CircleEntity(Entity):
    def __init__(self):
        super().__init__()
        self._type = 3
        self._x = 0
        self._y = 0
        self._radius = 0
        self._color = 0x0001

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        if value != self._x:
            self._x = value
            self._dirty = True

    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        if value != self._y:
            self._y = value
            self._dirty = True

    @property
    def x0(self):
        return self._x

    @property
    def y0(self):
        return self._y

    @property
    def x1(self):
        return self._x + self.diameter

    @property
    def y1(self):
        return self._y + self.diameter

    @property
    def radius(self):
        return self._radius
    @radius.setter
    def radius(self, value):
        if value != self._radius:
            self._radius = value
            self._dirty = True

    @property
    def diameter(self):
        return self._radius * 2

    @property
    def color(self):
        r = (self._color >> 11) & 0x1f
        g = (self._color >> 6) & 0x1f
        b = (self._color >> 1) & 0x1f
        r = ((r << 3) | (r >> 2)) & 0xff
        g = ((g << 3) | (g >> 2)) & 0xff
        b = ((b << 3) | (b >> 2)) & 0xff
        a = 0xff if (self._color & 1) else 0
        return (r, g, b, a)
    @color.setter
    def color(self, value):
        if len(value) == 3:
            value = value + (0xff,)
        if value != self.color:
            r = value[0] >> 3 & 0x1f
            g = value[1] >> 3 & 0x1f
            b = value[2] >> 3 & 0x1f
            a = value[3] >> 7 & 1
            self._color = (r << 11) | (g << 6) | (b << 1) | a
            self._dirty = True

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        bs.append(Bits(uint=int(self._x), length=12))
        bs.append(Bits(uint=int(self._y), length=12))
        bs.append(Bits(uint=int(self._radius), length=8))
        bs.append(Bits(uint=self._color, length=16))
        return bs

class TextEntity(Entity):
    def __init__(self):
        super().__init__()
        self._type = 4
        self._x = 0
        self._y = 0
        self._width = 0
        self._height = 0
        self._flags = 0
        self._color = 0x0001
        self._data = b'\0'

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        if value != self._x:
            self._x = value
            self._dirty = True

    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        if value != self._y:
            self._y = value
            self._dirty = True

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        if value != self._width:
            self._width = value
            self._dirty = True

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, value):
        if value != self._height:
            self._height = value
            self._dirty = True

    @property
    def color(self):
        r = (self._color >> 11) & 0x1f
        g = (self._color >> 6) & 0x1f
        b = (self._color >> 1) & 0x1f
        r = ((r << 3) | (r >> 2)) & 0xff
        g = ((g << 3) | (g >> 2)) & 0xff
        b = ((b << 3) | (b >> 2)) & 0xff
        a = 0xff if (self._color & 1) else 0
        return (r, g, b, a)
    @color.setter
    def color(self, value):
        if len(value) == 3:
            value = value + (0xff,)
        if value != self.color:
            r = value[0] >> 3 & 0x1f
            g = value[1] >> 3 & 0x1f
            b = value[2] >> 3 & 0x1f
            a = value[3] >> 7 & 1
            self._color = (r << 11) | (g << 6) | (b << 1) | a
            self._dirty = True

    @property
    def string(self):
        return self._data[:-1]
    @string.setter
    def string(self, value: str):
        if value != self.string:
            self._data = value.encode() + b'\0'
            self._dirty = True

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        bs.append(Bits(float16=self._x))
        bs.append(Bits(float16=self._y))
        bs.append(Bits(uint=int(self._width), length=12))
        bs.append(Bits(uint=int(self._height), length=12))
        bs.append(Bits(uint=self._flags, length=8))
        bs.append(Bits(uint=self._color, length=16))
        return bs
