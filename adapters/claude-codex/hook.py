#!/usr/bin/env python3
"""Forward main-agent Stop events to the shared tmux notifier."""
import json
import os
import subprocess
import sys


def main():
    agent = sys.argv[1] if len(sys.argv) == 2 else ""
    try:
        event = json.load(sys.stdin)
        if (
            agent in ("claude", "codex")
            and isinstance(event, dict)
            and event.get("hook_event_name") == "Stop"
            and not event.get("agent_id")
        ):
            notifier = os.path.join(
                os.path.expanduser("~"), ".config", "tmux", "agent-notify", "notify.sh"
            )
            subprocess.run([notifier, agent], stdin=subprocess.DEVNULL,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except (OSError, ValueError, TypeError):
        pass
    # Codex Stop requires valid JSON; this makes no decision and never continues a turn.
    if agent == "codex":
        print("{}")


if __name__ == "__main__":
    main()
