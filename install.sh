#!/bin/sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_TEMPLATE="$ROOT_DIR/com.controller.mxmaster-middle.plist"
PLIST_PATH="$HOME/Library/LaunchAgents/com.controller.mxmaster-middle.plist"
LOG_PATH="$HOME/Library/Logs/mxmaster-middle.log"
SCRIPT_PATH="$ROOT_DIR/mx_master_side_to_middle.py"
VENV_PATH="$ROOT_DIR/.venv"
PYTHON_PATH="$VENV_PATH/bin/python"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install it first: https://astral.sh/uv"
  exit 1
fi

if [ ! -d "$VENV_PATH" ]; then
  uv venv "$VENV_PATH"
fi

uv pip install --python "$PYTHON_PATH" pyobjc-framework-Quartz

sed -e "s|__SCRIPT_PATH__|$SCRIPT_PATH|g" \
    -e "s|__PYTHON_PATH__|$PYTHON_PATH|g" \
    -e "s|__LOG_PATH__|$LOG_PATH|g" \
    "$PLIST_TEMPLATE" > "$PLIST_PATH"

launchctl bootout "gui/$UID" "$PLIST_PATH" 2>/dev/null || true
launchctl bootstrap "gui/$UID" "$PLIST_PATH"
launchctl enable "gui/$UID/com.controller.mxmaster-middle"
launchctl kickstart -k "gui/$UID/com.controller.mxmaster-middle"

echo "Installed and started. Log: $LOG_PATH"
