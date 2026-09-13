"""Audit a proposed section against current runtime support before SD delivery.

This is a conversion/dependency gate, not a Wii fidelity or performance test.
No original assets are copied into the repository. Exit 1 means work remains.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from convert_course import decode_course
from inspect_assets import unpack_u8
from package_terrain import encode as terrain_encode
from package_enemies import encode as enemy_encode
from package_items import inventory, encode as item_encode
from route_section import SECTIONS, section_named
from package_checkpoint import encode as checkpoint_encode


def analyze(tiles, items, actors, entrances, section='checkpoint'):
    bounds = section_named(section)
    actors = [r for r in actors if r.get('area', 1) == 1]
    blockers = []
    deferred = []
    conversions = {}
    terrain = None
    try:
        terrain, omitted = terrain_encode(tiles, 0, section,actors)
        conversions['terrain'] = {'records': (len(terrain)-36)//12, 'omitted_markers': omitted,
                                  'capacity': 2048, 'status': 'convertible'}
    except (ValueError, KeyError) as error:
        blockers.append({'system': 'terrain', 'reason': str(error)})
    if terrain is not None:
        for name, convert in (
            ('enemies', lambda: enemy_encode(actors, terrain, section)),
            ('items', lambda: item_encode(items, actors, terrain, section=section)),
        ):
            try:
                data = convert()
                conversions[name] = {'records': (len(data)-24)//(8 if name == 'enemies' else 12),
                                     'status': 'convertible'}
            except (ValueError, KeyError) as error:
                blockers.append({'system': name, 'reason': str(error)})
    checkpoint_supported=False
    if section=='checkpoint' and terrain is not None:
        try:
            checkpoint_encode(actors,entrances,terrain)
            checkpoint_supported=True
            conversions['checkpoint']={'records':1,'status':'prototype; device/fidelity validation pending'}
        except (ValueError,KeyError) as error:
            blockers.append({'system':'checkpoint','reason':str(error)})

    # Examine the whole vertical route, including actors above the current view.
    chosen = [r for r in actors if bounds.x <= r['x'] < bounds.right]
    actor_report = []
    checkpoints = []
    for actor in chosen:
        actor_id = actor['id']
        row = {k: actor[k] for k in ('id', 'x', 'y', 'param')}
        if actor_id in (20, 57, 147) and bounds.contains(actor):
            row['status'] = 'converter_checked'
        elif actor_id==188 and checkpoint_supported:
            row['status']='prototype_checkpoint'
            deferred.append(dict(row,reason='Contact box, visual and restart behavior need integrated device/reference validation.'))
        elif actor_id==360 and (actor['x'],actor['y'],actor['param'])==(1904,544,0x0e000401):
            row['status']='static_pipe_hill_prototype'
            deferred.append(dict(row,reason='Requires bound NPH1/texture. Rotation, wall fidelity and entrance-4 bonus travel remain pending.'))
        elif actor_id==422 and bounds.contains(actor) and actor['param']==0 and actor.get('layer',0)==0:
            row['status']='ordinary_coin_block_no_rescue'
            deferred.append(dict(row,reason='Toad Rescue is inactive in this prototype; world-map rescue behavior remains pending.'))
        elif actor_id == 212 and (actor['x'], actor['y'], actor['param']) == (1456, 544, 0x01301801):
            row['status'] = 'opening_static_hill_only'
            deferred.append(dict(row, reason='Rotation, transport and final reference comparison remain deferred.'))
        elif actor_id in (310, 446, 477):
            row['status'] = 'deferred_review'
            deferred.append(dict(row, reason='Sign/background/Super Guide presentation or conditional activation review.'))
        else:
            row['status'] = 'requires_runtime_support'
            reason = {188: 'Checkpoint activation, entrance selection and death/restart persistence are not implemented.',
                      360: 'Eight-pipe hill needs a verified static surface/visual before route traversal; motion remains deferred.',
                      422: 'Toad block activation and reward conditions need verification.'}.get(
                          actor_id, 'Actor behavior is not covered by the current section runtime.')
            blockers.append(dict(row, system='actor', reason=reason))
        actor_report.append(row)
        if actor_id == 188:
            # Preserve every entrance candidate. Do not infer an ID from settings
            # before the source checkpoint-to-entrance rule is reconstructed.
            checkpoints.append(dict(row, entrance_candidates=[dict(e) for e in entrances
                if bounds.x <= e['x'] < bounds.right]))

    return {'schema_version': 1, 'section': section, 'runtime_profile': 'checkpoint-prototype-source',
            'source_bounds': [bounds.x, bounds.y, bounds.width, bounds.height],
            'ready_for_device_package': not blockers, 'conversions': conversions,
            'actor_counts': dict(sorted(Counter(str(r['id']) for r in chosen).items())),
            'actors': actor_report, 'checkpoints': checkpoints, 'blockers': blockers, 'deferred': deferred,
            'limitations': ['Passing this gate does not verify gameplay fidelity, graphics or 60 fps.',
                            'Hill instances whose anchors lie outside the section can overlap it; inspect boundaries before delivery.',
                            'All deferred entries require the final original-level comparison before completion.']}


def audit(extracted, tiles_path, output, section='checkpoint'):
    extracted, output = Path(extracted).resolve(), Path(output).resolve()
    if output.exists() or extracted == output or extracted in output.parents or output in extracted.parents:
        raise ValueError('Choose a new report path outside the extracted source')
    stage = (extracted/'files/Stage/01-01.arc').read_bytes()
    decoded = decode_course(unpack_u8(stage)['course/course1.bin'], {})
    records, actors = inventory(extracted)
    report = analyze(json.loads(Path(tiles_path).read_text()), records,
                     [r for r in actors if r['area'] == 1], decoded['entrances'], section)
    report['source_stage_sha256'] = hashlib.sha256(stage).hexdigest()
    report['terrain_inventory_sha256'] = hashlib.sha256(Path(tiles_path).read_bytes()).hexdigest()
    report['terrain_inventory_note'] = 'Use terrain.json generated from this extraction by convert_tiles; inventory hash is not source equivalence proof.'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('extracted', type=Path)
    parser.add_argument('tiles', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--section', choices=SECTIONS, default='checkpoint')
    args = parser.parse_args()
    try:
        result = audit(args.extracted, args.tiles, args.output, args.section)
        print(json.dumps({'report': str(args.output), 'ready': result['ready_for_device_package'],
                          'blockers': result['blockers']}, indent=2))
        raise SystemExit(0 if result['ready_for_device_package'] else 1)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(2, f'Route audit failed: {error}\n')
