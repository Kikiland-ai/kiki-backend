"""Build deterministic glTF 2.0 apparatus from semantic pack parts (no providers).

Metres, Y-up, named nodes, embedded buffers, no runtime CDN or renderer dependency.
Run from any directory; --check detects changed/missing assets without writing.
"""
import argparse
import base64
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1] / "prototypes/physical_labs"


def geometry(cylinder=False):
    positions, normals = [], []
    def triangle(vertices, normal):
        positions.extend(n for v in vertices for n in v)
        normals.extend(normal * 3)
    if cylinder:
        for i in range(24):
            a, b = i * math.tau / 24, (i + 1) * math.tau / 24
            x, z, u, v = .5 * math.cos(a), .5 * math.sin(a), .5 * math.cos(b), .5 * math.sin(b)
            normal = [math.cos((a + b) / 2), 0, math.sin((a + b) / 2)]
            triangle([(x, -.5, z), (x, .5, z), (u, .5, v)], normal)
            triangle([(x, -.5, z), (u, .5, v), (u, -.5, v)], normal)
            triangle([(0, .5, 0), (u, .5, v), (x, .5, z)], [0, 1, 0])
            triangle([(0, -.5, 0), (x, -.5, z), (u, -.5, v)], [0, -1, 0])
    else:
        for axis in range(3):
            for sign in (-1, 1):
                normal = [0, 0, 0]; normal[axis] = sign
                a, b = (axis + 1) % 3, (axis + 2) % 3
                vertices = []
                for u, v in ((-.5, -.5), (.5, -.5), (.5, .5), (-.5, .5)):
                    point = [0, 0, 0]; point[axis] = sign * .5; point[a] = u; point[b] = v
                    vertices.append(point)
                order = (0, 1, 2, 0, 2, 3) if sign == 1 else (0, 2, 1, 0, 3, 2)
                for n in range(0, 6, 3):
                    triangle([vertices[order[n + k]] for k in range(3)], normal)
    return positions, normals


def build(pack):
    design = {}
    if pack.get('visual_design'):
        path = ROOT / 'scene_designs' / pack['visual_design']
        if path.resolve().parent != (ROOT / 'scene_designs').resolve():
            raise ValueError('Visual design must remain in the scene catalogue')
        design = json.loads(path.read_text())
    palette = {"body": [.81, .79, .71, 1], "output": [.65, .12, .10, 1],
               "input": [.65, .12, .10, 1], "control": [.35, .37, .37, 1], "display": [.035, .09, .085, 1]}
    palette.update(design.get('materials', {}))
    buffer = bytearray(); views = []; accessors = []; shapes = []
    for cylinder in (False, True):
        positions, normals = geometry(cylinder)
        ids = []
        for values in (positions, normals):
            offset = len(buffer); data = struct.pack('<' + 'f' * len(values), *values); buffer.extend(data)
            views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(data), "target": 34962})
            accessor = {"bufferView": len(views) - 1, "componentType": 5126, "count": len(values) // 3, "type": "VEC3"}
            if values is positions:
                accessor.update({"min": [min(values[i::3]) for i in range(3)], "max": [max(values[i::3]) for i in range(3)]})
            accessors.append(accessor); ids.append(len(accessors) - 1)
        shapes.append(ids)
    materials = [{"name": kind, "pbrMetallicRoughness": {"baseColorFactor": colour,
                  "metallicFactor": .85 if kind in ('metal', 'pin') else 0,
                  "roughnessFactor": .28 if kind in ('metal', 'pin') else .68}} for kind, colour in palette.items()]
    meshes = []; nodes = []; cached = {}
    def add(name, position, size, shape, material, extras):
        key = (shape, material)
        if key not in cached:
            pos, normal = shapes[shape == 'cylinder']
            meshes.append({"name": shape + '-' + material, "primitives": [{"attributes": {"POSITION": pos, "NORMAL": normal},
                           "material": list(palette).index(material)}]})
            cached[key] = len(meshes) - 1
        nodes.append({"name": name, "mesh": cached[key], "translation": position, "scale": size, "extras": extras})
    for part in pack["parts"]:
        style = design.get('parts', {}).get(part['id'], {})
        shape = style.get('shape', 'cylinder' if part['kind'] in ('input', 'output', 'control') else 'cube')
        add(part['id'], part['position'], part['size'], shape, style.get('material', part['kind']),
            {"semanticTarget": part['id'], "label": part['label'], "kind": part['kind'],
             "layer": 0 if part['kind'] == 'body' else 3, **style})
    for detail in design.get('details', []):
        add(detail['id'], detail['position'], detail['size'], detail.get('shape', 'cube'), detail['material'],
            {"decorative": True, "layer": detail.get('layer', 3), "parentTarget": detail.get('parent'),
             "indicator": detail.get('indicator', False)})
    used = sorted({p['material'] for mesh in meshes for p in mesh['primitives']})
    material_indices = {old: new for new, old in enumerate(used)}
    materials = [materials[i] for i in used]
    for mesh in meshes:
        for primitive in mesh['primitives']:
            primitive['material'] = material_indices[primitive['material']]
    result = {"asset": {"version": "2.0", "generator": "Kiki semantic apparatus builder/v1",
                         "extras": {"fidelity": pack["review"]["geometry"], "equipment": pack["equipment"]["id"],
                                    "artwork": design.get('artwork', {}), "visualReferences": design.get('references', [])}},
              "scene": 0, "scenes": [{"nodes": list(range(len(nodes)))}], "nodes": nodes, "meshes": meshes,
              "materials": materials, "accessors": accessors, "bufferViews": views,
              "buffers": [{"byteLength": len(buffer), "uri": "data:application/octet-stream;base64," + base64.b64encode(buffer).decode()}]}
    return (json.dumps(result, separators=(",", ":")) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    for path in sorted((ROOT / 'packs').glob('*.json')):
        pack = json.loads(path.read_text()); data = build(pack)
        target = ROOT / 'assets' / pack['asset']
        if target.parent.resolve() != (ROOT / 'assets').resolve():
            raise ValueError('Asset must stay in catalogue')
        if args.check:
            if not target.is_file() or target.read_bytes() != data:
                raise SystemExit('Asset differs: ' + target.name)
            if pack.get('asset_sha256') != hashlib.sha256(data).hexdigest():
                raise SystemExit('Asset hash differs: ' + target.name)
        else:
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
            pack['asset_sha256'] = hashlib.sha256(data).hexdigest()
            path.write_text(json.dumps(pack, ensure_ascii=False, indent=2) + '\n')
        print(target.name, len(pack['parts']), 'semantic nodes', hashlib.sha256(data).hexdigest())


if __name__ == '__main__':
    main()
