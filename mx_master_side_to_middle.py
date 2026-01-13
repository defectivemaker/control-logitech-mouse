#!/usr/bin/env python3
import os
import sys
from Quartz import (
    CGEventTapCreate,
    CGEventTapEnable,
    CGEventGetIntegerValueField,
    CGEventSetIntegerValueField,
    CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource,
    CFRunLoopGetCurrent,
    CFRunLoopRun,
    kCFRunLoopCommonModes,
    kCGEventOtherMouseDown,
    kCGEventOtherMouseUp,
    kCGEventOtherMouseDragged,
    kCGEventTapDisabledByTimeout,
    kCGEventTapDisabledByUserInput,
    kCGEventTapOptionDefault,
    kCGHeadInsertEventTap,
    kCGHIDEventTap,
    kCGMouseButtonCenter,
    kCGMouseEventButtonNumber,
    CGEventMaskBit,
)

SOURCE_BUTTON = int(os.environ.get("MX_SOURCE_BUTTON", "4"))
TARGET_BUTTON = int(os.environ.get("MX_TARGET_BUTTON", str(kCGMouseButtonCenter)))

_tap = None


def _remap_event(event_type, event):
    if event_type not in (
        kCGEventOtherMouseDown,
        kCGEventOtherMouseUp,
        kCGEventOtherMouseDragged,
    ):
        return event

    button = CGEventGetIntegerValueField(event, kCGMouseEventButtonNumber)
    if button != SOURCE_BUTTON:
        return event

    CGEventSetIntegerValueField(event, kCGMouseEventButtonNumber, TARGET_BUTTON)
    return event


def _event_callback(proxy, event_type, event, refcon):
    if event_type in (kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput):
        CGEventTapEnable(_tap, True)
        return event

    return _remap_event(event_type, event)


def main():
    global _tap
    event_mask = (
        CGEventMaskBit(kCGEventOtherMouseDown)
        | CGEventMaskBit(kCGEventOtherMouseUp)
        | CGEventMaskBit(kCGEventOtherMouseDragged)
    )

    _tap = CGEventTapCreate(
        kCGHIDEventTap,
        kCGHeadInsertEventTap,
        kCGEventTapOptionDefault,
        event_mask,
        _event_callback,
        None,
    )

    if _tap is None:
        sys.stderr.write(
            "Failed to create event tap. Enable Accessibility permissions for this script.\n"
        )
        return 1

    run_loop_source = CFMachPortCreateRunLoopSource(None, _tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), run_loop_source, kCFRunLoopCommonModes)
    CGEventTapEnable(_tap, True)

    CFRunLoopRun()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
