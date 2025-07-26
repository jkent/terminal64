__all__ = ['clamp', 'vlq_pack', 'vlq_unpack']

def clamp(value, min_, max_):
    return min(max_, max(min_, value))

def vlq_pack(value):
    data = bytearray()
    while len(data) < 5:
        byte = value & 0x7f
        data.insert(0, byte)
        value >>= 7
        if not value:
            for i in range(len(data) - 1):
                data[i] |= 0x80
            return data
    else:
        raise OverflowError

def vlq_unpack(data):
    value = 0
    length = 0
    for byte in data:
        value |= byte & 0x7f
        length += 1
        if not byte & 0x80:
            return value, length
        if length >= 5:
            raise OverflowError
        value <<= 7
    raise IndexError
