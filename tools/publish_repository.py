#!/usr/bin/env python3
"""Publish the asset-free build kit to your empty private GitHub repository."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*command, capture=False):
    result = subprocess.run(command, cwd=ROOT, check=True, text=True,
                            stdout=subprocess.PIPE if capture else None)
    return result.stdout if capture else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='omarkebrit/gta5-ios-port-audited')
    args = parser.parse_args()
    repo = json.loads(run('gh', 'api', f'repos/{args.repo}', capture=True))
    if not repo.get('private') or not repo.get('permissions', {}).get('push'):
        parser.error('the repository must be private and writable with your gh login')
    run('gh', 'auth', 'setup-git')
    existing = run('git', 'ls-remote', f'https://github.com/{args.repo}.git', 'refs/heads/*', capture=True)
    if existing.strip():
        parser.error('the repository is not empty; send its URL to the assistant to finish without overwriting it')
    if not (ROOT / '.git').exists():
        run('git', 'init', '-b', 'main')
        # Explicitly add source roots; never add game directories or local build outputs.
        run('git', 'add', '.github', '.gitignore', '.gitattributes', 'app', 'audit', 'docs', 'tools',
            'README.md', 'README-AUDITED.md', 'LICENSE', 'CHANGELOG.md', 'build_ipa.sh')
        # ZIP downloads on Windows lose Unix executable mode.
        run('git', 'update-index', '--chmod=+x', 'build_ipa.sh')
        run('git', '-c', 'user.name=Build kit import', '-c', 'user.email=build-kit@local.invalid',
            'commit', '-m', 'Import audited upstream source and private iOS build workflows')
    changes = run('git', 'status', '--porcelain', capture=True)
    if changes.strip():
        parser.error('source tree has uncommitted changes; commit the intended source changes before publishing')
    run('git', 'push', f'https://github.com/{args.repo}.git', 'HEAD:main')
    print(f'Published source: https://github.com/{args.repo}')
    print(f'Source checks: https://github.com/{args.repo}/actions/workflows/audit.yml')


if __name__ == '__main__':
    main()
