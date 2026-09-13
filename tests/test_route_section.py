from pathlib import Path
import struct
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from route_section import section_named
from package_terrain import encode as terrain_encode
from package_enemies import encode as enemy_encode
from package_items import encode as item_encode
from audit_route import analyze


def tile(x=496, tile_id=1):
    return dict(x=x, y=480, slot=0, tile=tile_id, layer=1,
                flags='0000000100000000', collision='solid', shape=0)


def actor(kind, x, param=0):
    return dict(area=1, kind=1, id=kind, x=x, y=464, param=param, layer=0)


class RouteSectionTests(unittest.TestCase):
    def test_shared_bounds_and_crop_edges(self):
        records = [tile(x) for x in (480, 496, 1888, 1904, 3296, 3312)]
        opening = terrain_encode(records, 0)[0]
        extended = terrain_encode(records, 0, 'checkpoint')[0]
        self.assertEqual(struct.unpack_from('<II', opening, 8), (2, 1408))
        self.assertEqual(struct.unpack_from('<II', extended, 8), (4, 2816))
        self.assertEqual([r[0] for r in struct.iter_unpack('<HHHBBBBH', extended[36:])], [0, 1392, 1408, 2800])
        with self.assertRaises(ValueError):
            enemy_encode([], extended)  # Cannot bind an opening package to the longer section.
        with self.assertRaises(ValueError):
            section_named('typo')

    def test_real_source_koopa_coordinates_and_variants(self):
        terrain = terrain_encode([tile()], 0, 'checkpoint')[0]
        data = enemy_encode([actor(57, 2192), actor(57, 2720, 1), actor(20, 3312)], terrain, 'checkpoint')
        self.assertEqual(list(struct.iter_unpack('<4H', data[24:])), [(1696, 80, 57, 0), (2224, 80, 57, 1)])
        for settings in (2, 16, 65536, -1):
            with self.assertRaises(ValueError):
                enemy_encode([actor(57, 2192, settings)], terrain, 'checkpoint')

    def test_extended_reward_is_not_silently_dropped(self):
        terrain = terrain_encode([tile(2704, 48)], 0, 'checkpoint')[0]
        item = dict(area=1, x=2704, y=480, tile=48, contents=2)
        data = item_encode([item], [], terrain, section='checkpoint')
        self.assertEqual(struct.unpack_from('<3HBBI', data, 24), (2208,96,0,3,2,0))
        item['contents']=3
        with self.assertRaisesRegex(ValueError, 'contents 3.*2704,480'):
            item_encode([item], [], terrain, section='checkpoint')
        item['contents'] = 0
        data = item_encode([item], [], terrain, section='checkpoint')
        self.assertEqual(struct.unpack_from('<3HBBI', data, 24), (2208, 96, 0, 3, 0, 0))

    def test_audit_identifies_runtime_dependencies(self):
        actors = [actor(57, 2192), actor(188, 3184, 65536), actor(360, 1904), actor(422, 2208)]
        report = analyze([tile()], [], actors, [dict(id=1, x=3104, y=416,type=0,flags=0,destination_file=0,destination_id=0,layer=0)], 'checkpoint')
        self.assertFalse(report['ready_for_device_package'])
        self.assertEqual(report['conversions']['enemies']['records'], 1)
        self.assertEqual({r['id'] for r in report['blockers'] if 'id' in r}, {360})
        self.assertEqual(report['checkpoints'][0]['entrance_candidates'][0]['id'], 1)

    def test_out_of_view_and_unknown_actors_are_accounted_for(self):
        upper = actor(999, 2100); upper['y'] = 272
        report = analyze([tile()], [], [upper, actor(57, 3312)], [], 'checkpoint')
        self.assertEqual(report['actor_counts'], {'999': 1})
        self.assertTrue(any(r.get('id') == 999 for r in report['blockers']))

    def test_corrupt_binding_and_capacity_fail_closed(self):
        terrain = bytearray(terrain_encode([tile()], 0, 'checkpoint')[0]); terrain[-1] ^= 1
        with self.assertRaises(ValueError):
            enemy_encode([], terrain, 'checkpoint')
        with self.assertRaises(ValueError):
            terrain_encode([tile()]*2049, 0, 'checkpoint')


if __name__ == '__main__':
    unittest.main()
