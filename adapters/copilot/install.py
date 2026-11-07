#!/usr/bin/env python3
"""Install or remove the tmux agent-notify Copilot CLI hook."""
import argparse
import json
import os
from pathlib import Path
import sys


SOURCE = Path(__file__).with_name("hook.py")
HANDLER = Path.home() / ".config/tmux/agent-notify/copilot/hook.py"


def hook_path():
    home = Path(os.environ.get("COPILOT_HOME") or Path.home() / ".copilot")
    return home / "hooks" / "tmux-agent-notify.json"


def hook_content():
    config = {
        "version": 1,
        "hooks": {
            "agentStop": [{"type": "command", "exec": "python3", "args": [str(HANDLER)]}]
        },
    }
    return (json.dumps(config, indent=2) + "\n").encode("utf-8")


def check_owned(path, content):
    if path.is_symlink():
        raise ValueError(f"refusing to modify symlink: {path}")
    if path.exists() and (not path.is_file() or path.read_bytes() != content):
        raise ValueError(f"refusing to modify existing file: {path}")


def create(path, content):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        check_owned(path, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    args = parser.parse_args()
    try:
        path = hook_path()
        handler = SOURCE.read_bytes()
        config = hook_content()
        check_owned(path, config)
        check_owned(HANDLER, handler)
        if args.action == "install":
            create(HANDLER, handler)
            create(path, config)
        else:
            path.unlink(missing_ok=True)
            HANDLER.unlink(missing_ok=True)
        print(f"copilot: {args.action} {path}")
    except (OSError, ValueError) as error:
        print(f"agent-notify: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
