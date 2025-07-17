import struct
from types import SimpleNamespace

COMM_ENTITY = 0

class Color:
    def __init__(self, **kw):
        self._r = 0x00
        self._g = 0x00
        self._b = 0x00
        self._a = 0x00
        self.__dict__.update({f'_{k}': v for k, v in kw.items()})

    @property
    def r(self):
        return self._r
    @r.setter
    def r(self, value):
        value = int(value)
        if value != self.r:
            self._r = value
            self._parent._dirty = True

    @property
    def g(self):
        return self._g
    @g.setter
    def g(self, value):
        value = int(value)
        if value != self.g:
            self._g = value
            self._parent._dirty = True

    @property
    def b(self):
        return self._b
    @b.setter
    def b(self, value):
        value = int(value)
        if value != self.b:
            self._b = value
            self._parent._dirty = True

    @property
    def a(self):
        return self._a
    @a.setter
    def a(self, value):
        value = int(value)
        if value != self.a:
            self._a = value
            self._parent._dirty = True

    @property
    def tuple(self):
        return (self.r, self.g, self.b, self.a)
    @tuple.setter
    def tuple(self, value):
        if value != (self.r, self.g, self.b, self.a):
            self.r, self.g, self.b, self.a = value
            self._parent._dirty = True

    @property
    def value(self):
        return int.from_bytes(struct.pack('>BBBB', *self.tuple), 'big')
    @value.setter
    def value(self, value):
        self.tuple = struct.unpack('>BBBB', value.to_bytes(4, 'big'))

class Rect:
    def __init__(self, **kw):
        self._x = 0
        self._y = 0
        self._width = 0
        self._height = 0
        self.__dict__.update({f'_{k}': v for k, v in kw.items()})

    @property
    def x(self):
        return self._x
    @x.setter
    def x(self, value):
        value = int(value)
        if value != self.x:
            self._x = value
            self._parent._dirty = True

    @property
    def y(self):
        return self._y
    @y.setter
    def y(self, value):
        value = int(value)
        if value != self.y:
            self._y = value
            self._parent._dirty = True

    @property
    def width(self):
        return self._width
    @width.setter
    def width(self, value):
        value = int(value)
        if value != self.width:
            self._width = value
            self._parent._dirty = True

    @property
    def height(self):
        return self._height
    @height.setter
    def height(self, value):
        value = int(value)
        if value != self.height:
            self._height = value
            self._parent._dirty = True

    @property
    def tuple(self):
        return (self._x, self._y, self._width, self._height)
    @tuple.setter
    def tuple(self, value):
        if value != (self.x, self.y, self.width, self.height):
            self.x, self.y, self.width, self.height = value
            self._parent._dirty = True

    @property
    def bbox(self):
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    @property
    def value(self):
        return int.from_bytes(struct.pack('>HHHH', *self.tuple), 'big')
    @value.setter
    def value(self, value):
        self.tuple = struct.unpack('>HHHH', value.to_bytes(8, 'big'))

class Entity:
    next_id = 0
    types = {
        'none': 0,
        'rect': 1,
        'ball': 2,
        'text': 3,
    }

    def __init__(self, **kw):
        self._type = 'none'
        self._flags = 0
        self._rect = Rect(**kw)
        self._color = Color(**kw)
        self._data = b''
        self.__dict__.update({f'_{k}': v for k, v in kw.items()})
        self._rect._parent = self
        self._color._parent = self
        self._dirty = True

    @property
    def id(self):
        return self._id

    @property
    def type(self):
        return self._type
    @type.setter
    def rect(self, value):
        if self._type != value:
            self._type = value
            self._dirty = True

    @property
    def flags(self):
        return self._flags
    @flags.setter
    def flags(self, value):
        if self._flags != value:
            self._flags= value
            self._dirty = True

    @property
    def rect(self):
        return self._rect
    @rect.setter
    def rect(self, value):
        self._rect = value
        self._rect._parent = self
        self._dirty = True

    @property
    def color(self):
        return self._color
    @color.setter
    def color(self, value):
        self._color = value
        self._color._parent = self
        self._dirty = True

    @property
    def data(self):
        return self._data
    @data.setter
    def data(self, value):
        if self._data != value:
            self._data = value
            self._dirty = True
            self._data_dirty = True

    @property
    def text(self):
        return self.data.decode()
    @text.setter
    def text(self, value):
        self.data = value.encode()

    @property
    def dirty(self):
        return self._dirty

    @property
    def packet(self):
        id = self.__dict__.setdefault('_id', Entity.next_id)
        if id == Entity.next_id:
            Entity.next_id += 1
        type = Entity.types[self.type]

        pkt = struct.pack('>IHHQI', id, type, self.flags, self.rect.value,
                          self.color.value) + self._data
        pkt = struct.pack('>HH', len(pkt), COMM_ENTITY) + pkt
        self._dirty = False
        return pkt
