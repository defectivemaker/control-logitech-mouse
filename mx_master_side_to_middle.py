#!/usr/bin/env python3
import os
import sys
from Quartz import (
    CGEventCreateScrollWheelEvent,
    CGEventGetFlags,
    CGEventTapCreate,
    CGEventTapEnable,
    CGEventGetIntegerValueField,
    CGEventSetFlags,
    CGEventSetIntegerValueField,
    CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource,
    CFRunLoopGetCurrent,
    CFRunLoopRun,
    kCFRunLoopCommonModes,
    kCGEventOtherMouseDown,
    kCGEventOtherMouseUp,
    kCGEventOtherMouseDragged,
    kCGEventScrollWheel,
    kCGEventTapDisabledByTimeout,
    kCGEventTapDisabledByUserInput,
    kCGEventTapOptionDefault,
    kCGEventSourceStateID,
    kCGEventSourceUnixProcessID,
    kCGEventSourceUserData,
    kCGEventTargetUnixProcessID,
    kCGSessionEventTap,
    kCGHeadInsertEventTap,
    kCGTailAppendEventTap,
    kCGHIDEventTap,
    kCGMouseButtonCenter,
    kCGMouseEventButtonNumber,
    kCGScrollEventUnitLine,
    kCGScrollEventUnitPixel,
    kCGScrollWheelEventDeltaAxis1,
    kCGScrollWheelEventDeltaAxis2,
    kCGScrollWheelEventDeltaAxis3,
    kCGScrollWheelEventInstantMouser,
    kCGScrollWheelEventIsContinuous,
    kCGScrollWheelEventMomentumPhase,
    kCGScrollWheelEventPointDeltaAxis1,
    kCGScrollWheelEventPointDeltaAxis2,
    kCGScrollWheelEventPointDeltaAxis3,
    kCGScrollWheelEventScrollPhase,
    CGEventMaskBit,
)

SOURCE_BUTTON = int(os.environ.get("MX_SOURCE_BUTTON", "4"))
TARGET_BUTTON = int(os.environ.get("MX_TARGET_BUTTON", str(kCGMouseButtonCenter)))


def _env_bool(name, default):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in ("0", "false", "no", "off", "")


REVERSE_SCROLL = _env_bool("MX_REVERSE_SCROLL", True)
# By default only reverse wheel-like mouse scroll events (e.g., Logitech),
# while preserving natural direction for continuous devices such as trackpads.
REVERSE_SCROLL_CONTINUOUS = _env_bool("MX_REVERSE_SCROLL_CONTINUOUS", False)
PREFERRED_TAP = os.environ.get("MX_EVENT_TAP", "hid").strip().lower()
PREFERRED_PLACEMENT = os.environ.get("MX_EVENT_TAP_PLACEMENT", "tail").strip().lower()
DEBUG_SCROLL = _env_bool("MX_DEBUG_SCROLL", False)
_debug_scroll_count = 0

_tap = None


def _should_reverse_scroll(event):
    if not REVERSE_SCROLL:
        return False

    if REVERSE_SCROLL_CONTINUOUS:
        return True

    scroll_phase = CGEventGetIntegerValueField(event, kCGScrollWheelEventScrollPhase)
    momentum_phase = CGEventGetIntegerValueField(event, kCGScrollWheelEventMomentumPhase)
    # Trackpad-like gestures carry phase/momentum metadata; skip those.
    if scroll_phase != 0 or momentum_phase != 0:
        return False

    instant_mouser = CGEventGetIntegerValueField(event, kCGScrollWheelEventInstantMouser)
    if instant_mouser != 0:
        return True

    is_continuous = CGEventGetIntegerValueField(event, kCGScrollWheelEventIsContinuous)
    return is_continuous == 0


def _build_reversed_scroll_event(event):
    axis1 = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis1)
    axis2 = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis2)
    axis3 = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis3)

    if axis1 == 0 and axis2 == 0 and axis3 == 0:
        axis1 = CGEventGetIntegerValueField(event, kCGScrollWheelEventPointDeltaAxis1)
        axis2 = CGEventGetIntegerValueField(event, kCGScrollWheelEventPointDeltaAxis2)
        axis3 = CGEventGetIntegerValueField(event, kCGScrollWheelEventPointDeltaAxis3)
        unit = kCGScrollEventUnitPixel
    else:
        is_continuous = CGEventGetIntegerValueField(event, kCGScrollWheelEventIsContinuous)
        unit = kCGScrollEventUnitPixel if is_continuous != 0 else kCGScrollEventUnitLine

    if axis1 == 0 and axis2 == 0 and axis3 == 0:
        return event

    reversed_event = CGEventCreateScrollWheelEvent(None, unit, 3, -axis1, -axis2, -axis3)
    if reversed_event is None:
        return event

    CGEventSetFlags(reversed_event, CGEventGetFlags(event))
    return reversed_event


def _remap_event(event_type, event):
    global _debug_scroll_count
    if event_type in (
        kCGEventOtherMouseDown,
        kCGEventOtherMouseUp,
        kCGEventOtherMouseDragged,
    ):
        button = CGEventGetIntegerValueField(event, kCGMouseEventButtonNumber)
        if button != SOURCE_BUTTON:
            return event

        CGEventSetIntegerValueField(event, kCGMouseEventButtonNumber, TARGET_BUTTON)
        return event

    if event_type != kCGEventScrollWheel:
        return event

    if DEBUG_SCROLL and _debug_scroll_count < 50:
        is_continuous = CGEventGetIntegerValueField(event, kCGScrollWheelEventIsContinuous)
        instant_mouser = CGEventGetIntegerValueField(event, kCGScrollWheelEventInstantMouser)
        phase = CGEventGetIntegerValueField(event, kCGScrollWheelEventScrollPhase)
        momentum = CGEventGetIntegerValueField(event, kCGScrollWheelEventMomentumPhase)
        axis1 = CGEventGetIntegerValueField(event, kCGScrollWheelEventDeltaAxis1)
        point1 = CGEventGetIntegerValueField(event, kCGScrollWheelEventPointDeltaAxis1)
        source_pid = CGEventGetIntegerValueField(event, kCGEventSourceUnixProcessID)
        target_pid = CGEventGetIntegerValueField(event, kCGEventTargetUnixProcessID)
        source_state = CGEventGetIntegerValueField(event, kCGEventSourceStateID)
        source_user_data = CGEventGetIntegerValueField(event, kCGEventSourceUserData)
        sys.stderr.write(
            "scroll event: "
            f"source_pid={source_pid} target_pid={target_pid} "
            f"source_state={source_state} source_user_data={source_user_data} "
            f"is_continuous={is_continuous} instant_mouser={instant_mouser} "
            f"phase={phase} momentum={momentum} "
            f"delta1={axis1} point1={point1}\n"
        )
        _debug_scroll_count += 1

    if not _should_reverse_scroll(event):
        return event

    return _build_reversed_scroll_event(event)


def _event_callback(proxy, event_type, event, refcon):
    if event_type in (kCGEventTapDisabledByTimeout, kCGEventTapDisabledByUserInput):
        CGEventTapEnable(_tap, True)
        return event

    return _remap_event(event_type, event)


def main():
    global _tap
    tap_placement = kCGTailAppendEventTap
    if PREFERRED_PLACEMENT == "head":
        tap_placement = kCGHeadInsertEventTap

    event_mask = (
        CGEventMaskBit(kCGEventOtherMouseDown)
        | CGEventMaskBit(kCGEventOtherMouseUp)
        | CGEventMaskBit(kCGEventOtherMouseDragged)
        | CGEventMaskBit(kCGEventScrollWheel)
    )

    tap_order = [kCGHIDEventTap, kCGSessionEventTap]
    if PREFERRED_TAP == "session":
        tap_order = [kCGSessionEventTap, kCGHIDEventTap]
    elif PREFERRED_TAP == "hid":
        tap_order = [kCGHIDEventTap, kCGSessionEventTap]

    for tap_location in tap_order:
        _tap = CGEventTapCreate(
            tap_location,
            tap_placement,
            kCGEventTapOptionDefault,
            event_mask,
            _event_callback,
            None,
        )
        if _tap is not None:
            sys.stderr.write(
                f"Using tap location: {tap_location}, placement: {tap_placement}\n"
            )
            break

    if _tap is None:
        sys.stderr.write(
            "Failed to create event tap (HID + Session). Enable Accessibility permissions for this script.\n"
        )
        return 1

    run_loop_source = CFMachPortCreateRunLoopSource(None, _tap, 0)
    CFRunLoopAddSource(CFRunLoopGetCurrent(), run_loop_source, kCFRunLoopCommonModes)
    CGEventTapEnable(_tap, True)

    CFRunLoopRun()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
