# MX Master 3S Side Button -> Middle Click (macOS)

This runs a small background process that remaps the far side button on a Logitech MX Master 3S to a middle click.

## Requirements

- macOS 14+ (you are on 14.1.1)
- `uv` installed

If you need `uv`:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup

1. Grant Accessibility permissions to the `python` inside this repo's venv:
   - System Settings -> Privacy & Security -> Accessibility
   - Add `.../control-logitech-mouse/.venv/bin/python`.
   - You may also need Input Monitoring on some systems.
2. Install and start the launch agent:

```
./install.sh
```

This loads `~/Library/LaunchAgents/com.controller.mxmaster-middle.plist` and keeps the process running at login.
`install.sh` uses `uv` to create `.venv` and install `pyobjc-framework-Quartz`.

## Adjusting the button

If the far side button does not remap, try changing `MX_SOURCE_BUTTON` from `4` to `3` in the launch agent:

```
~/Library/LaunchAgents/com.controller.mxmaster-middle.plist
```

Then reload:

```
launchctl bootout "gui/$UID" ~/Library/LaunchAgents/com.controller.mxmaster-middle.plist
launchctl bootstrap "gui/$UID" ~/Library/LaunchAgents/com.controller.mxmaster-middle.plist
launchctl kickstart -k "gui/$UID/com.controller.mxmaster-middle"
```

## Uninstall

```
./uninstall.sh
```
