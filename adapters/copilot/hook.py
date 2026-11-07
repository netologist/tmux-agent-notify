#!/usr/bin/env python3
"""Forward root Copilot CLI agent-stop events to the shared notifier."""
import json
from pathlib import Path
import subprocess
import sys


def main():
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict) or event.get("stopReason") != "end_turn":
            return
        if any(key in event for key in ("agentId", "agentType", "parentAgentId", "agent_id", "agent_type", "parent_agent_id")):
            return
        notifier = Path.home() / ".config/tmux/agent-notify/notify.sh"
        subprocess.run([str(notifier), "copilot"], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=False)
    except (OSError, ValueError):
        # A notification must never interfere with the agent's turn.
        pass


if __name__ == "__main__":
    main()
