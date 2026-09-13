"""Shared, bounded World 1-1 conversion coordinates (not gameplay readiness)."""
from dataclasses import dataclass
import struct
from convert_course import fnv1a


@dataclass(frozen=True)
class Section:
    name: str
    right: int
    x: int = 496
    y: int = 384
    height: int = 320
    spawn_x: int = 256
    spawn_y: int = 192

    @property
    def width(self):
        return self.right-self.x

    def contains(self, record):
        return self.x <= record['x'] < self.right and self.y <= record['y'] < self.y+self.height

    def validate_terrain(self, terrain):
        if len(terrain) < 36 or terrain[:4] != b'NST1' or struct.unpack_from('<I', terrain, 4)[0] != 1:
            raise ValueError('Expected NST1 version 1')
        count = struct.unpack_from('<I', terrain, 8)[0]
        if not 0 < count <= 2048 or len(terrain) != 36+12*count:
            raise ValueError('Invalid terrain record count/length')
        if struct.unpack_from('<4I', terrain, 12) != (self.width, self.height, self.spawn_x, self.spawn_y):
            raise ValueError(f'Terrain bounds/spawn do not match section {self.name}')
        if fnv1a(terrain[:32]+terrain[36:]) != struct.unpack_from('<I', terrain, 32)[0]:
            raise ValueError('Terrain checksum mismatch')


SECTIONS = {'opening': Section('opening', 1904), 'checkpoint': Section('checkpoint', 3312)}


def section_named(name):
    try:
        return SECTIONS[name]
    except KeyError:
        raise ValueError(f'Unknown route section: {name}') from None
