class Sprite:
    def __init__(self, path=None):
        self.clear()
        if path:
            self.load(path)

    @property
    def dirty(self):
        return self._dirty

    def clear(self):
        self._data = b''
        self._dirty = True

    def load(self, path):
        with open(path, 'rb') as f:
            self._data = f.read()
        self._dirty = True

    def message(self, i):
        self._dirty = False
        return i.to_bytes(2) + self._data
