#!/bin/sh
set -euo pipefail

PLIST_PATH="$HOME/Library/LaunchAgents/com.controller.mxmaster-middle.plist"

if [ -f "$PLIST_PATH" ]; then
  launchctl bootout "gui/$UID" "$PLIST_PATH" 2>/dev/null || true
  rm -f "$PLIST_PATH"
  echo "Uninstalled launch agent."
else
  echo "Launch agent not found."
fi
