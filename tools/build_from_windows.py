#!/usr/bin/env python3
"""Validate a lawful game folder, upload the small private input ZIP and dispatch CI."""
import argparse
import importlib.util
import json
from pathlib import Path
import secrets
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('minimal_inputs', ROOT / 'app/Scripts/minimal_inputs.py')
inputs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inputs)


def gh(*args, capture=False):
    result = subprocess.run(['gh', *args], check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout if capture else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-folder', type=Path, required=True, help='folder containing data/ and b/')
    parser.add_argument('--repo', default='omarkebrit/gta5-ios-port-audited')
    parser.add_argument('--paid', action='store_true', help='request memory entitlements for a paid Apple team')
    parser.add_argument('--prepare-only', action='store_true', help='create the local ZIP without contacting GitHub')
    args = parser.parse_args()
    if not args.prepare_only:
        if not shutil.which('gh'):
            parser.error('install GitHub CLI and run gh auth login first')
        repo = json.loads(gh('api', f'repos/{args.repo}', capture=True))
        if not repo.get('private'):
            parser.error('the destination must be a private repository')
        if not repo.get('permissions', {}).get('push'):
            parser.error('your GitHub login does not have write access to the destination')
    archive = ROOT / 'app/Build/Upload/gta5-build-inputs.zip'
    try:
        receipt = inputs.pack(args.game_folder.resolve(), archive)
    except (OSError, ValueError, KeyError, IndexError) as error:
        parser.exit(1, f'Cannot build from this folder: {error}\n')
    print(f"Prepared {receipt['files']} files; {receipt['zip_bytes'] / 1048576:.1f} MiB uploaded. The data archives stay on your PC.", flush=True)
    if args.prepare_only:
        print(archive)
        print(json.dumps(receipt))
        return
    tag = 'build-inputs-' + secrets.token_hex(8)
    gh('release', 'create', tag, str(archive), '--repo', args.repo, '--target', 'main',
       '--title', 'Temporary private build inputs', '--prerelease',
       '--notes', 'User-supplied engine, manifest and shader packs only. Deleted automatically after a successful build; retained after failure for debugging.')
    gh('workflow', 'run', 'build-ipa.yml', '--repo', args.repo, '--ref', 'main',
       '-f', f'input_release={tag}', '-f', f"input_sha256={receipt['sha256']}",
       '-f', 'paid_account=' + ('true' if args.paid else 'false'))
    print(f'Build started: https://github.com/{args.repo}/actions/workflows/build-ipa.yml')
    print(f'Inputs: https://github.com/{args.repo}/releases/tag/{tag}')
    print('After success, download GTA5Port-ipa from the run. If the build fails, keep the private input release while debugging.')


if __name__ == '__main__':
    try:
        main()
    except (OSError, subprocess.CalledProcessError) as error:
        sys.exit(f'Build submission stopped: {error}. Check your GitHub login and repository access.')
