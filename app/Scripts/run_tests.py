#!/usr/bin/env python3
"""Run every independent checked-in test, recording blocked tests explicitly."""
import collections
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Build/Audit'
PORTABLE = {'asset_hints', 'controller_look', 'engine_configuration', 'memory_budget',
            'packed_asset_cache', 'frame_metrics', 'frame_rate', 'ring_packets', 'bc_textures'}
BLOCKED = {
    'asset_pipeline': 'Requires the real generated game.h and a configured HTTP range server.',
    'frame_reports': 'Missing Source/NativeFrameReports.inc (legacy renderer test).',
    'metal_buffer_cache': 'Missing PlayGTA5MetalBufferCache.h.',
    'native_uniform_resolver': 'Missing webgpu.h and NativeUniforms.inc (legacy renderer test).',
    'prepared_draws': 'Missing webgpu.h and NativeUniforms/NativePipelineCache/NativePreparedDraws.inc.',
    'state_packing': 'Missing Resources/gpu-batch.js (legacy renderer test).',
    'texture_rows': 'Missing Source/NativeTextureRows.h.',
    'texture_views': 'Missing Source/NativeTextureView.h.',
    'warm_dispatch': 'WarmDispatchHarness.inc references removed WebGPU renderer files.',
    'warm_javascript': 'WarmDispatchHarness.inc references removed WebGPU renderer files.',
}


def execute(command, log):
    result = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, timeout=180)
    log.write(result.stdout)
    return result.returncode


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mac_arm = platform.system() == 'Darwin' and platform.machine() == 'arm64'
    results = []
    for source in sorted((ROOT / 'Tests').iterdir()):
        if source.suffix not in ('.c', '.cpp', '.m', '.mm'):
            continue
        name = source.stem
        reason = BLOCKED.get(name)
        if not reason and name not in PORTABLE and not mac_arm:
            reason = 'Requires macOS/Apple Silicon, Xcode, WABT and SIMDe.'
        if reason:
            results.append({'test': name, 'status': 'blocked', 'reason': reason})
            print(f'BLOCKED {name}: {reason}', flush=True)
            continue
        with (OUT / (name + '.log')).open('w') as log:
            try:
                if name == 'native_runtime':
                    status = execute(['sh', 'Scripts/check_runtime.sh'], log)
                else:
                    cpp = source.suffix in ('.cpp', '.mm')
                    compiler = ['xcrun', 'clang++' if cpp else 'clang'] if mac_arm else [
                        shutil.which('g++' if cpp else 'gcc') or ('g++' if cpp else 'gcc')]
                    binary = OUT / name
                    command = compiler + ['-std=c++20' if cpp else '-std=c11', '-O2',
                                          '-D_DEFAULT_SOURCE', '-I', 'Source', str(source), '-o', str(binary)]
                    if name == 'bc_textures':
                        command += ['Source/BCTextureDecoder.c', '-lm']
                    if name == 'controller_look':
                        command += ['-lm']
                    if name == 'arm_shared_simd':
                        command += ['-I', 'Tools/wabt-1.0.42/include', '-I', 'Tools/simde']
                    status = execute(command, log)
                    if status == 0:
                        status = execute([str(binary)], log)
                results.append({'test': name, 'status': 'passed' if status == 0 else 'failed',
                                'exit_code': status})
            except (OSError, subprocess.TimeoutExpired) as error:
                log.write(str(error))
                results.append({'test': name, 'status': 'failed', 'reason': str(error)})
        print(results[-1]['status'].upper(), name, flush=True)
    summary = dict(collections.Counter(item['status'] for item in results))
    (OUT / 'test-results.json').write_text(json.dumps({
        'platform': platform.platform(), 'machine': platform.machine(),
        'summary': summary, 'tests': results}, indent=2) + '\n')
    print(json.dumps(summary))
    return 1 if summary.get('failed') else 0


if __name__ == '__main__':
    sys.exit(main())
