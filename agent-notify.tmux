#!/bin/sh
# TPM entry point: define a platform default without overriding user settings.
case "$(uname -s)" in
  Darwin) default_sound=/System/Library/Sounds/Glass.aiff ;;
  Linux) default_sound=/usr/share/sounds/freedesktop/stereo/complete.oga ;;
  *) exit 0 ;;
esac
tmux set-option -goq @agent-notify-sound "$default_sound"
