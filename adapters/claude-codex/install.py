#!/usr/bin/env python3
"""Install or remove only this project's Claude Code and Codex Stop hooks."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


SOURCE = Path(__file__).with_name("hook.py")
DEST = Path.home() / ".config/tmux/agent-notify/claude-codex/hook.py"


def settings_path(agent):
    if agent == "claude":
        return Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude") / "settings.json"
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "hooks.json"


def entry(agent):
    command = 'python3 "$HOME/.config/tmux/agent-notify/claude-codex/hook.py" ' + agent
    return {"hooks": [{"type": "command", "command": command}]}


def load(path):
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return data


def update(data, agent, install):
    if "hooks" not in data:
        if not install:
            return False
        data["hooks"] = {}
    hooks = data["hooks"]
    if not isinstance(hooks, dict):
        raise ValueError("settings hooks must be a JSON object")
    if "Stop" not in hooks:
        if not install:
            return False
        hooks["Stop"] = []
    stops = hooks["Stop"]
    if not isinstance(stops, list):
        raise ValueError("settings hooks.Stop must be a JSON array")
    own = entry(agent)
    if install:
        if own in stops:
            return False
        stops.append(own)
    else:
        if own not in stops:
            return False
        stops[:] = [item for item in stops if item != own]
        if not stops:
            del hooks["Stop"]
        if not hooks:
            del data["hooks"]
    return True


def save(path, data):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    fd, temporary = tempfile.mkstemp(prefix=".agent-notify-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), mode)
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def install_handler():
    content = SOURCE.read_bytes()
    DEST.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        with DEST.open("xb") as target:
            target.write(content)
    except FileExistsError:
        if DEST.is_symlink() or DEST.read_bytes() != content:
            raise ValueError(f"refusing to overwrite existing handler: {DEST}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("agent", choices=("claude", "codex"))
    args = parser.parse_args()
    try:
        path = settings_path(args.agent)
        data = load(path)
        changed = update(data, args.agent, args.action == "install")
        if args.action == "install":
            install_handler()
        if changed:
            save(path, data)
        print(f"{args.agent}: {'updated' if changed else 'unchanged'} {path}")
    except (OSError, ValueError) as error:
        print(f"agent-notify: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
