from bitstring import Bits, BitStream

from .display import disp_height, disp_width
from ..util import clamp

SKIP_ENTITY         = 0
SPRITE_ENTITY       = 1
RECTANGLE_ENTITY    = 2
CIRCLE_ENTITY       = 3
TEXT_ENTITY         = 4


class BBox:
    def __init__(self):
        self._x = 0
        self._y = 0
        self._width = 1
        self._height = 1
        self._dirty = True

    @property
    def min_x(self):
        return 0

    @property
    def min_y(self):
        return 0

    @property
    def max_x(self):
        return disp_width - self.width

    @property
    def max_y(self):
        return disp_height - self.height

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def x0(self):
        return self.x

    @property
    def y0(self):
        return self.y

    @property
    def x1(self):
        return self.x + self.width

    @property
    def y1(self):
        return self.y + self.height

class Entity(BBox):
    def __init__(self):
        super().__init__()
        self._type = SKIP_ENTITY
        self._dirty = True
        self._data = b''

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self, value):
        if value != self.type:
            self._type = value
            self._dirty = True

    @property
    def dirty(self):
        return self._dirty

    @BBox.x.setter
    def x(self, value):
        value = clamp(value, self.min_x, self.max_x)
        if value != self.x:
            self._x = value
            self._dirty = True

    @BBox.y.setter
    def y(self, value):
        value = clamp(value, self.min_y, self.max_y)
        if value != self.y:
            self._y = value
            self._dirty = True

    @BBox.width.setter
    def width(self, value):
        if value != self.width:
            self._width = value
            self.x = self._x
            self._dirty = True

    @BBox.height.setter
    def height(self, value):
        if value != self.height:
            self._height = value
            self.y = self._y
            self._dirty = True

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        return bs

    def message(self, i):
        self._dirty = False
        return i.to_bytes(2) + self.bitstream.bytes + self._data

class SpriteEntity(Entity):
    def __init__(self):
        super().__init__()
        self._type = SPRITE_ENTITY
        self._index = 0
        self._tile = 0
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
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        bs.append(Bits(uint=self._index, length=8))
        bs.append(Bits(uint=self._tile, length=8))
        bs.append(Bits(float16=self.x))
        bs.append(Bits(float16=self.y))
        bs.append(Bits(uint=self.flags, length=8))
        bs.append(Bits(uint=int(self.cx), length=8))
        bs.append(Bits(uint=int(self.cy), length=8))
        bs.append(Bits(float16=self.scale_x))
        bs.append(Bits(float16=self.scale_y))
        bs.append(Bits(float16=self.theta))
        return bs

class SolidEntity(Entity):
    def __init__(self):
        super().__init__()
        self._color = 0xffff

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
            value = value + (255,)
        if value != self.color:
            r = value[0] >> 3 & 0x1f
            g = value[1] >> 3 & 0x1f
            b = value[2] >> 3 & 0x1f
            a = value[3] >> 7 & 1
            self._color = (r << 11) | (g << 6) | (b << 1) | a
            self._dirty = True

class RectangleEntity(SolidEntity):
    def __init__(self):
        super().__init__()
        self._type = RECTANGLE_ENTITY

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        bs.append(Bits(uint=int(self.x0), length=12))
        bs.append(Bits(uint=int(self.y0), length=12))
        bs.append(Bits(uint=int(self.x1), length=12))
        bs.append(Bits(uint=int(self.y1), length=12))
        bs.append(Bits(uint=self._color, length=16))
        return bs

class CircleEntity(SolidEntity):
    def __init__(self):
        super().__init__()
        self._type = CIRCLE_ENTITY
        self._radius = 0.5

    @property
    def radius(self):
        return self._radius
    @radius.setter
    def radius(self, value):
        if value != self._radius:
            self._radius = value
            self._width = value * 2
            self._height = value * 2
            self._dirty = True

    @property
    def diameter(self):
        return self._radius * 2

    @property
    def bitstream(self):
        bs = BitStream()
        bs.append(Bits(uint=self._type, length=8))
        bs.append(Bits(uint=int(self.x), length=12))
        bs.append(Bits(uint=int(self.y), length=12))
        bs.append(Bits(uint=int(self.radius), length=8))
        bs.append(Bits(uint=self._color, length=16))
        return bs

class TextEntity(SolidEntity):
    def __init__(self, string=None):
        super().__init__()
        self._type = TEXT_ENTITY
        self._flags = 0
        self._data = b'\0'
        if string is not None:
            self.string = string

    @property
    def flags(self):
        return self._flags

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
        bs.append(Bits(float16=self.x))
        bs.append(Bits(float16=self.y))
        bs.append(Bits(uint=int(self.width), length=12))
        bs.append(Bits(uint=int(self.height), length=12))
        bs.append(Bits(uint=self.flags, length=8))
        bs.append(Bits(uint=self._color, length=16))
        return bs
