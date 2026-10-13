#!/usr/bin/env python3
"""Pack or unpack only the engine, manifest and indexed shader packs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

ENGINE = 'b/8b0b5899ed/game.wasm'
SHADERS = 'b/8b0b5899ed/shaders/'
INDEX = SHADERS + 'index.json'
MANIFEST = 'data/manifest.json'
ENGINE_HASH = '11ca8d2c04c5e843d18ff4aea4899d72c86973c6b031df334e67c446b2ae83e0'
INDEX_HASH = '11c331895051b30126980ef666bd8935314ab400348b17c56ef8fe8983f50ee0'
LIMIT = 1024 ** 3


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def required_files(engine, index_data, manifest_data):
    if hashlib.sha256(engine).hexdigest() != ENGINE_HASH:
        raise ValueError('game.wasm does not match the supported WebAssembly build; PC GTA5.exe is not a substitute')
    if hashlib.sha256(index_data).hexdigest() != INDEX_HASH:
        raise ValueError('shader index does not match build 8b0b5899ed')
    index = json.loads(index_data)
    names = [ENGINE, INDEX, MANIFEST]
    for pack in index['_packs']:
        name = pack['file']
        if not isinstance(name, str) or PurePosixPath(name).name != name or '\\' in name or name in ('.', '..'):
            raise ValueError('unsafe shader pack name')
        names.append(SHADERS + name)
    manifest = json.loads(manifest_data)
    if not isinstance(manifest.get('files'), list) or not manifest['files']:
        raise ValueError('manifest.json has no game file list')
    for entry in manifest['files']:
        if not isinstance(entry, list) or len(entry) < 2 or not isinstance(entry[0], str):
            raise ValueError('invalid manifest entry')
        path = PurePosixPath(entry[0].replace('\\', '/'))
        if path.is_absolute() or '..' in path.parts or ':' in entry[0] or '\0' in entry[0]:
            raise ValueError('unsafe manifest path')
        if not isinstance(entry[1], int) or entry[1] < 0:
            raise ValueError('invalid game file size in manifest')
    return names, index


def validate_ranges(index, sizes):
    for name, item in index.items():
        if name.startswith('_') or not item.get('ok') or 'p' not in item:
            continue
        number, offset, wgsl_size, constants_size = item['p']
        if any(not isinstance(x, int) or x < 0 for x in (number, offset, wgsl_size, constants_size)):
            raise ValueError('invalid shader pack range')
        pack = index['_packs'][number]['file']
        if offset + wgsl_size + constants_size > sizes[SHADERS + pack]:
            raise ValueError(f'shader pack {pack} is truncated')


def pack(mirror, destination):
    names, index = required_files((mirror / ENGINE).read_bytes(),
                                  (mirror / INDEX).read_bytes(), (mirror / MANIFEST).read_bytes())
    sizes = {name: (mirror / name).stat().st_size for name in names}
    if sum(sizes.values()) > LIMIT:
        raise ValueError('minimal build inputs unexpectedly exceed 1 GiB')
    validate_ranges(index, sizes)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, compresslevel=1) as archive:
        for name in names:
            archive.write(mirror / name, name)
    return {'files': len(names), 'input_bytes': sum(sizes.values()),
            'zip_bytes': destination.stat().st_size, 'sha256': digest_file(destination)}


def unpack(source, destination):
    with zipfile.ZipFile(source) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError('duplicate ZIP entries')
        if sum(x.file_size for x in archive.infolist()) > LIMIT:
            raise ValueError('input ZIP expands beyond 1 GiB')
        names, index = required_files(archive.read(ENGINE), archive.read(INDEX), archive.read(MANIFEST))
        if set(archive.namelist()) != set(names):
            raise ValueError('input ZIP must contain exactly the minimal build files, without game archives or extras')
        sizes = {name: archive.getinfo(name).file_size for name in names}
        validate_ranges(index, sizes)
        for name in names:
            mode = archive.getinfo(name).external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError('symlinks are not supported')
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(name) as src, target.open('wb') as dst:
                for block in iter(lambda: src.read(1024 * 1024), b''):
                    dst.write(block)
    subprocess.run([sys.executable, str(Path(__file__).with_name('check_game_files.py')),
                    '--mirror', str(destination)], check=True)
    return {'files': len(names), 'input_bytes': sum(sizes.values()), 'sha256': digest_file(source)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('pack')
    p.add_argument('--mirror', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p = commands.add_parser('unpack')
    p.add_argument('--zip', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = pack(args.mirror, args.out) if args.command == 'pack' else unpack(args.zip, args.out)
    except (OSError, ValueError, KeyError, IndexError, zipfile.BadZipFile) as error:
        parser.exit(1, f'Build inputs rejected: {error}\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
