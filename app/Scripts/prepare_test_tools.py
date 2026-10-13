#!/usr/bin/env python3
"""Prepare open-source test dependencies without any game files."""
import argparse
import hashlib
from pathlib import Path
import platform
import subprocess
import tarfile
import urllib.request

from safe_extract import extract

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'Tools'


def download(url, destination):
    with urllib.request.urlopen(url, timeout=120) as response:
        destination.write_bytes(response.read())


def run(*command):
    subprocess.run(command, cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--portable', action='store_true', help='only the BC decoder dependency')
    args = parser.parse_args()
    TOOLS.mkdir(exist_ok=True)
    commit = '80859ed3b7afb1c527a2a99d70c61457bea72d0c'
    bcdec = TOOLS / 'bcdec'
    if not bcdec.exists():
        archive = TOOLS / 'bcdec.tar.gz'
        download(f'https://codeload.github.com/iOrange/bcdec/tar.gz/{commit}', archive)
        with tarfile.open(archive) as package:
            extract(package, TOOLS)
        (TOOLS / f'bcdec-{commit}').rename(bcdec)
    if args.portable:
        return
    if platform.system() != 'Darwin' or platform.machine() != 'arm64':
        parser.error('the full runtime tests require an Apple Silicon Mac')
    wabt = TOOLS / 'wabt-1.0.42'
    if not wabt.exists():
        base = 'https://github.com/WebAssembly/wabt/releases/download/1.0.42/'
        filename = 'wabt-1.0.42-macos-arm64.tar.gz'
        archive = TOOLS / filename
        download(base + filename, archive)
        with urllib.request.urlopen(base + filename + '.sha256', timeout=120) as response:
            expected = response.read().decode().split()[0]
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise SystemExit('WABT archive checksum mismatch')
        with tarfile.open(archive) as package:
            extract(package, TOOLS)
    if not (TOOLS / 'simde').exists():
        run('git', 'clone', '--depth', '1', '--branch', 'v0.8.2',
            'https://github.com/simd-everywhere/simde.git', str(TOOLS / 'simde'))
    for remote, local in [('src/c-writer.cc', 'c-writer-original.cc'),
                          ('src/tools/wasm2c.cc', 'wasm2c-main.cc')]:
        download('https://raw.githubusercontent.com/WebAssembly/wabt/1.0.42/' + remote, TOOLS / local)
    run('python3', 'Scripts/patch_wasm2c.py')
    run('xcrun', 'clang', '-Wno-deprecated-declarations', '-c',
        'Scripts/sha256_shim.c', '-o', 'Tools/sha256_shim.o')
    run('xcrun', 'clang++', '-std=c++20', '-O1', '-I', str(wabt / 'include'),
        'Tools/wasm2c-main.cc', 'Tools/c-writer-patched.cc', 'Tools/sha256_shim.o',
        str(wabt / 'lib/libwabt.a'), '-o', 'Tools/wasm2c-native')
    runtime = wabt / 'share/wabt/wasm2c/wasm-rt-impl.c'
    source = runtime.read_text()
    if 'pg_record_trap' not in source:
        anchor = 'void wasm_rt_trap(wasm_rt_trap_t code) {'
        if source.count(anchor) != 1:
            raise SystemExit('WABT trap diagnostic patch no longer matches')
        source = source.replace(anchor, 'extern void pg_record_trap(int) __attribute__((weak));\n' +
                                anchor + '\n  if(pg_record_trap)pg_record_trap(code);')
        runtime.write_text(source)


if __name__ == '__main__':
    main()
