#!/bin/sh
# Agent adapters call this after a user-facing turn finishes.
[ -n "${TMUX:-}" ] && [ -n "${TMUX_PANE:-}" ] || exit 0
case "${1:-}" in omp|pi|claude|codex|opencode|copilot|gemini|agy) agent=$1 ;; *) exit 2 ;; esac
command -v tmux >/dev/null 2>&1 || exit 0
tmux display-message -p -t "$TMUX_PANE" '#{pane_id}' >/dev/null 2>&1 || exit 0

tmux display-message -t "$TMUX_PANE" "${agent}: turn ended"
sound=$(tmux show-options -gv @agent-notify-sound 2>/dev/null)
[ "$sound" = off ] && exit 0
if command -v afplay >/dev/null 2>&1; then
  [ -n "$sound" ] || sound=/System/Library/Sounds/Glass.aiff
  [ ! -f "$sound" ] || afplay "$sound" >/dev/null 2>&1 &
elif command -v paplay >/dev/null 2>&1; then
  [ -n "$sound" ] || sound=/usr/share/sounds/freedesktop/stereo/complete.oga
  [ ! -f "$sound" ] || paplay "$sound" >/dev/null 2>&1 &
fi
