#!/usr/bin/env python3
"""Install tmux-agent-notify adapters without replacing existing extensions."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
HOME = Path.home()
BASE = HOME / '.config/tmux/agent-notify'
AGENTS = ('omp', 'pi', 'claude', 'codex', 'opencode')


def extension_path(agent):
    if agent in ('omp', 'pi'):
        if os.environ.get('PI_CODING_AGENT_DIR'):
            raise ValueError('PI_CODING_AGENT_DIR is set; install with separate default Pi and OMP directories')
        return HOME / ('.omp' if agent == 'omp' else '.pi') / 'agent/extensions/tmux-agent-notify.ts'
    xdg = Path(os.environ.get('XDG_CONFIG_HOME') or HOME / '.config')
    return xdg / 'opencode/plugins/tmux-agent-notify.ts'


def install_file(source, dest, executable=False):
    data = source.read_bytes()
    if dest.exists() or dest.is_symlink():
        if dest.is_symlink() or not dest.is_file() or dest.read_bytes() != data:
            raise ValueError(f'refusing to overwrite {dest}')
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as target:
            target.write(data)
    if executable:
        dest.chmod(dest.stat().st_mode | 0o111)
    print(f'installed {dest}')


def uninstall_file(source, dest):
    if not dest.exists() and not dest.is_symlink():
        return
    if dest.is_symlink() or not dest.is_file() or dest.read_bytes() != source.read_bytes():
        raise ValueError(f'refusing to remove modified file {dest}')
    dest.unlink()
    print(f'removed {dest}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('install', 'uninstall'))
    parser.add_argument('agents', nargs='+', choices=(*AGENTS, 'all'))
    args = parser.parse_args()
    agents = AGENTS if 'all' in args.agents else tuple(dict.fromkeys(args.agents))
    if args.action == 'install':
        install_file(ROOT / 'notify.sh', BASE / 'notify.sh', True)
    for agent in agents:
        if agent in ('claude', 'codex'):
            subprocess.run([sys.executable, str(ROOT / 'adapters/claude-codex/install.py'), args.action, agent], check=True)
        else:
            source = ROOT / 'adapters/agents' / f'{agent}.ts'
            dest = extension_path(agent)
            (install_file if args.action == 'install' else uninstall_file)(source, dest)
    if args.action == 'uninstall':
        print('Shared notifier retained for any other installed adapters.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'tmux-agent-notify: {error}', file=sys.stderr)
        sys.exit(1)
