#!/usr/bin/env python3
"""Install or remove the Gemini CLI or Antigravity CLI turn-end hook."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys
import tempfile


NAME = "tmux-agent-notify"


def settings_path(agent):
    if agent == "gemini":
        return Path(os.environ.get("GEMINI_CLI_HOME") or Path.home()) / ".gemini/settings.json"
    return Path.home() / ".gemini/config/hooks.json"


def handler(agent):
    response = '{"decision":"allow"}' if agent == "agy" else '{}'
    command = ('~/.config/tmux/agent-notify/notify.sh ' + agent
               + " >/dev/null 2>&1; printf '" + response + "\\n'")
    return {"type": "command", "command": command}


def load(path):
    if path.is_symlink():
        raise ValueError(f"refusing to replace symlink: {path}")
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return data


def update_gemini(data, install):
    if "hooks" not in data:
        if not install:
            return False
        data["hooks"] = {}
    hooks = data["hooks"]
    if not isinstance(hooks, dict):
        raise ValueError("settings hooks must be a JSON object")
    if "AfterAgent" not in hooks:
        if not install:
            return False
        hooks["AfterAgent"] = []
    events = hooks["AfterAgent"]
    if not isinstance(events, list):
        raise ValueError("settings hooks.AfterAgent must be a JSON array")
    own = {"hooks": [{**handler("gemini"), "name": NAME}]}
    # Refuse to modify an independently edited or conflicting named hook.
    matches = [group for group in events if isinstance(group, dict) and
               isinstance(group.get("hooks"), list) and any(
                   isinstance(h, dict) and h.get("name") == NAME
                   for h in group["hooks"])]
    if any(group != own for group in matches):
        raise ValueError(f"refusing to modify conflicting hook: {NAME}")
    if install:
        if matches:
            return False
        events.append(own)
    else:
        if not matches:
            return False
        events[:] = [group for group in events if group != own]
        if not events:
            del hooks["AfterAgent"]
        if not hooks:
            del data["hooks"]
    return True


def update_agy(data, install):
    own = {"Stop": [handler("agy")]}
    if NAME in data and data[NAME] != own:
        raise ValueError(f"refusing to modify conflicting hook: {NAME}")
    if install:
        if NAME in data:
            return False
        data[NAME] = own
    else:
        if NAME not in data:
            return False
        del data[NAME]
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("agent", choices=("gemini", "agy"))
    args = parser.parse_args()
    try:
        path = settings_path(args.agent)
        data = load(path)
        update = update_gemini if args.agent == "gemini" else update_agy
        changed = update(data, args.action == "install")
        if changed:
            save(path, data)
        print(f"{args.agent}: {'updated' if changed else 'unchanged'} {path}")
    except (OSError, ValueError) as error:
        print(f"agent-notify: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
