# tmux-agent-notify

Play a sound and show a tmux message when a coding agent's turn ends, without scraping terminal output. Native agent hooks report the event; tmux identifies the pane. The agent stays open. A turn ending may mean an error or cancellation, not necessarily success.

## Supported agents

| Agent | Event | Notes |
| --- | --- | --- |
| OMP | `agent_end` | Interactive main agent only; ignores known continuations and nested OMP sessions. |
| Pi | `agent_settled` | Interactive sessions; waits for retries and queued continuations. |
| Claude Code | `Stop` | Main agent, not `SubagentStop`. |
| Codex | `Stop` | Start with `codex --no-daemon` so the hook inherits the correct pane; trust the hook when prompted. |
| OpenCode | `session.status` | Root session transitions from busy to idle; launch the OpenCode server in the intended tmux pane. |
| GitHub Copilot CLI | `agentStop` | User-level hook; ignores subagent events. |
| Gemini CLI | `AfterAgent` | Runs after a response; another hook may request a retry. |
| Antigravity CLI (`agy`) | `Stop` | Execution-loop stop; can also run for other Antigravity surfaces sharing its hook configuration. |

Claude, Codex, Copilot, Gemini and Antigravity can run other completion hooks that continue or retry a turn after this hook fires; an early or repeated notification is possible. Gemini and Antigravity do not document parent/subagent identifiers for these events, so subagent notifications cannot be reliably filtered. Copilot's sandbox may need access to the installed notifier and tmux socket. OpenCode's server environment belongs to the server process, so an externally shared server cannot reliably attribute an event to a particular client pane. Run one server in the intended pane. OMP and Pi adapters only notify for interactive TUI sessions. Hooks or plugins disabled by an agent's policy cannot run.

## Requirements

- tmux and Python 3; agent-specific extensions/hooks must be enabled.
- macOS: `afplay` and a system sound. Linux: `paplay` and the freedesktop sound theme. Without a sound player/file, the tmux message still works.
- Agent and tmux must run on the machine that should play the sound. Remote agent processes cannot play local audio without separate forwarding.

## Install

From this directory:

```sh
python3 install.py install all
# Or select agents:
python3 install.py install omp claude
```

The installer copies the notifier to `~/.config/tmux/agent-notify/` and installs selected adapters in the agents' standard user configuration directories. Claude, Codex, Gemini and Antigravity hooks are merged with existing settings; Copilot uses its own hook file. Existing unrelated extension files are never overwritten. Restart the agents after installation. A running OMP/Pi process does not load an extension installed after startup. If Codex asks to trust the new hook, review it in `/hooks` and approve it.

`PI_CODING_AGENT_DIR` overrides Pi/OMP's default directories. Unset it when installing both; sharing the same extension directory between Pi and OMP is unsafe. `CLAUDE_CONFIG_DIR`, `CODEX_HOME`, `COPILOT_HOME`, `GEMINI_CLI_HOME` and `XDG_CONFIG_HOME` are honored for Claude, Codex, Copilot, Gemini and OpenCode respectively. Gemini defaults to `~/.gemini/settings.json`; Antigravity uses `~/.gemini/config/hooks.json`. The notifier itself is installed under `$HOME/.config/tmux`.

To load the tmux plugin entry point, add this to `tmux.conf` and reload:

```tmux
run-shell '~/.config/tmux/agent-notify/agent-notify.tmux'
```

The entry point sets the platform's default sound only if the option is unset. Installing the agent adapters is still required.

### tmux popups

A popup may inherit `TMUX` but not `TMUX_PANE`. Start the popup from a `run-shell` binding so tmux expands the pane ID before passing it as an environment variable:
```tmux
bind -n M-p run-shell -b "tmux display-popup -E -e 'TMUX_PANE=#{pane_id}' omp"
```

For a popup that should start in the current pane directory, use:
```tmux
bind -n M-p run-shell -b "tmux display-popup -E -d \"\$(tmux display-message -p -t '#{pane_id}' '##{pane_current_path}')\" -e 'TMUX_PANE=#{pane_id}' omp"
```

## Sound

Set a custom absolute sound file in `tmux.conf`, then reload tmux:

```tmux
set -g @agent-notify-sound '/path/to/sound.aiff'
```

Set it to `off` to silence the sound while retaining tmux messages. The default is macOS `Glass.aiff`, or Linux `complete.oga` when `paplay` is available. The player must support the file format.

## Uninstall

```sh
python3 install.py uninstall all
# Or select agents:
python3 install.py uninstall omp claude
```

Only matching installed adapter files and this project's hook entries are removed. The shared notifier and Claude/Codex hook handler remain, so removing one agent never breaks another. Remove `~/.config/tmux/agent-notify/` manually after uninstalling every adapter if no other configuration uses it.

## Security and scope

Agent prompts, responses and credentials are not sent to the notifier. It receives only an agent name and inherited tmux context. It runs no model calls and does nothing outside tmux. The installer refuses to overwrite changed adapter files or settings symlinks; inspect conflicts before changing them. This project does not auto-install dependencies or alter your tmux configuration.

## License

MIT; see [LICENSE](LICENSE).
