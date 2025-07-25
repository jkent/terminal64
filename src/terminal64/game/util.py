from bitstring import ConstBitStream
from types import SimpleNamespace

def collision(a, b):
    return a.x0 <= b.x1 and a.x1 >= b.x0 and a.y0 <= b.y1 and a.y1 >= b.y0

def decode_input(data):
    bitstream = ConstBitStream(data)
    namespace = SimpleNamespace()
    namespace.a        = bitstream.read(1).u
    namespace.b        = bitstream.read(1).u
    namespace.z        = bitstream.read(1).u
    namespace.start    = bitstream.read(1).u
    namespace.d_up     = bitstream.read(1).u
    namespace.d_down   = bitstream.read(1).u
    namespace.d_left   = bitstream.read(1).u
    namespace.d_right  = bitstream.read(1).u
    namespace.y        = bitstream.read(1).u
    namespace.x        = bitstream.read(1).u
    namespace.l        = bitstream.read(1).u
    namespace.r        = bitstream.read(1).u
    namespace.c_up     = bitstream.read(1).u
    namespace.c_down   = bitstream.read(1).u
    namespace.c_left   = bitstream.read(1).u
    namespace.c_right  = bitstream.read(1).u
    namespace.stick_x  = bitstream.read(8).i
    namespace.stick_y  = bitstream.read(8).i
    namespace.cstick_x = bitstream.read(8).i
    namespace.cstick_y = bitstream.read(8).i
    namespace.analog_l = bitstream.read(8).i
    namespace.analog_r = bitstream.read(8).i
    return namespace
