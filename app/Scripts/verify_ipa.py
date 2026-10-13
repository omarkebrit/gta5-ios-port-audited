#!/usr/bin/env python3
"""Static packaging checks only: these cannot prove installation or gameplay."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import plistlib
import struct
import zipfile


def verify(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP CRC check failed')
        names = archive.namelist()
        apps = {PurePosixPath(n).parts[1] for n in names if n.startswith('Payload/') and
                len(PurePosixPath(n).parts) > 1 and PurePosixPath(n).parts[1].endswith('.app')}
        if len(apps) != 1:
            raise ValueError('IPA must have exactly one Payload/*.app')
        prefix = 'Payload/' + apps.pop() + '/'
        info = plistlib.loads(archive.read(prefix + 'Info.plist'))
        if info.get('CFBundleSupportedPlatforms') != ['iPhoneOS']:
            raise ValueError('app is not an iPhoneOS device build')
        if not info.get('CFBundleIdentifier') or info.get('UIDeviceFamily') != [1, 2]:
            raise ValueError('missing bundle identity or wrong device family')
        executable = archive.read(prefix + info['CFBundleExecutable'])
        magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from('<8I', executable)
        if magic != 0xFEEDFACF or cpu != 0x0100000C or kind != 2:
            raise ValueError('main executable is not a thin ARM64 Mach-O executable')
        offset = 32
        ios_device = False
        for _ in range(count):
            command, length = struct.unpack_from('<II', executable, offset)
            if length < 8 or offset + length > len(executable):
                raise ValueError('invalid Mach-O load command')
            if command == 0x32:
                ios_device = struct.unpack_from('<I', executable, offset + 8)[0] == 2
            if command == 0x25:
                ios_device = True
            if command == 0x2C and struct.unpack_from('<I', executable, offset + 16)[0] != 0:
                raise ValueError('main executable is encrypted')
            offset += length
        if not ios_device:
            raise ValueError('main executable lacks an iOS device deployment command')
        for resource in ('manifest.json', 'shaders-iphoneos.metallib', 'shader-reflection.jsonl', '_CodeSignature/CodeResources'):
            if prefix + resource not in names or archive.getinfo(prefix + resource).file_size == 0:
                raise ValueError(f'missing or empty required resource: {resource}')
        if any(n.lower().endswith(('.wasm', '.rpf')) for n in names):
            raise ValueError('raw engine/game archives unexpectedly bundled')
        if any('/data/x64/' in n or '/data/common/' in n for n in names):
            raise ValueError('large game data unexpectedly bundled')
    return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size,
            'bundle_identifier': info['CFBundleIdentifier'], 'minimum_ios': info.get('MinimumOSVersion'),
            'architecture': 'arm64', 'platform': 'iPhoneOS',
            'status': 'static checks passed; requires Apple ID re-signing and physical-device testing'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ipa', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.ipa)
    except (OSError, ValueError, KeyError, IndexError, struct.error, zipfile.BadZipFile) as error:
        parser.exit(1, f'IPA verification failed: {error}\n')
    output = json.dumps(result, indent=2) + '\n'
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output)
    print(output)


if __name__ == '__main__':
    main()
