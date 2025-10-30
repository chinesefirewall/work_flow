"""
A small, Windows-friendly Python script that types text or simulates key presses every N seconds
for a configurable duration, then exits. Works with Google Sheets, Excel, Notepad, etc. (active window must be focused).

Quick start (newbie-friendly):
- Open this file and look for the section: "User-configurable defaults (easy to edit)" near the top.
- Change the DEFAULT_* values to set what happens when you just run the script.
- Current defaults: TYPE into the active window every 5 seconds for 3 hours.

Usage examples (from a terminal or small IDE run configuration):

1) Print to console every 5 seconds for 1 minute (default message):
   python work_flow.py --duration 60 --interval 5 --mode print

2) TYPE into the currently active window every 5 seconds for 2 minutes:
   python work_flow.py --duration 120 --interval 5 --mode type --action type --message "Still here"

3) Type a slash into Google Sheets without pressing Enter (lets you open shortcuts):
   python work_flow.py --duration 60 --interval 5 --mode type --action type --message "/" --no-enter

4) PRESS keys: save in Excel every 30s using Ctrl+S (Windows):
   python work_flow.py --duration 600 --interval 30 --mode type --action press --keys "ctrl+s"

5) PRESS a sequence: go down then enter in Google Sheets every 5s:
   python work_flow.py --duration 60 --interval 5 --mode type --action press --keys "down,enter"

Notes:
- For typing/pressing to work, the active window (e.g., Notepad/Excel/Browser) must be focused.
- If pyautogui isn't installed or available, the script will automatically fall back to printing what it would do.
- Stop early with Ctrl+C.

Arguments:
- --duration   Total run time in seconds (default: 60)
- --interval   Seconds between each action (default: 5)
- --mode       One of: auto|type|print (default: auto) — controls whether we use pyautogui or print
- --action     One of: type|press (default: type)
- --message    Text to type (for --action type) (default: "Hello from work_flow")
- --no-enter   When set, do not press Enter after typing text (useful for typing "/" in Sheets)
- --keys       Keys to press (for --action press). Examples: "enter", "ctrl+s", "down,enter"

Windows notes:
- No admin rights are required. Works on standard Windows accounts.
- Keep your target window focused to receive keystrokes.
"""
from __future__ import annotations

import argparse
import sys
import time
import threading
from datetime import datetime
from typing import Optional

# === User-configurable defaults (easy to edit) ===
# Set what the script does by default when you just run it without CLI flags.
# Default behavior: TYPE into the currently active window every 5 seconds for 3 hours.
DEFAULT_DURATION_SECONDS = 3 * 60 * 60  # 3 hours
DEFAULT_INTERVAL_SECONDS = 5            # seconds between actions
DEFAULT_MODE = "type"                   # 'type' tries to control the keyboard via pyautogui
DEFAULT_ACTION = "type"                 # 'type' to type text, 'press' to press keys
DEFAULT_MESSAGE = "Hello from work_flow"  # text used when action is 'type'
DEFAULT_NO_ENTER = False                 # if True, do NOT press Enter after typing
DEFAULT_KEYS = "enter"                   # keys used when action is 'press' (e.g., "ctrl+s", "down,enter")


def _try_import_pyautogui():
    try:
        import pyautogui  # type: ignore
        # Make pyautogui a bit safer; moving mouse to a corner can abort if fail-safe is enabled.
        pyautogui.FAILSAFE = True
        return pyautogui
    except Exception:
        return None


def _type_message(pyautogui, msg: str, press_enter: bool = True) -> bool:
    try:
        # Type the message into the currently active window and optionally press Enter
        pyautogui.typewrite(msg, interval=0.02)
        if press_enter:
            pyautogui.press("enter")
        return True
    except Exception:
        return False


def _press_keys(pyautogui, keys_spec: str) -> bool:
    """
    Press keys according to a simple spec:
    - Single key: "enter", "f2", "down"
    - Chord with '+': "ctrl+s", "ctrl+shift+v"
    - Sequence with commas: "down,enter" (processed left-to-right)
    """
    try:
        spec = keys_spec.strip()
        if not spec:
            return False
        # Split into sequence steps by comma
        steps = [s.strip() for s in spec.split(',') if s.strip()]
        for step in steps:
            if '+' in step:
                parts = [p.strip() for p in step.split('+') if p.strip()]
                if not parts:
                    continue
                # pyautogui.hotkey handles chords
                pyautogui.hotkey(*parts)
            else:
                pyautogui.press(step)
        return True
    except Exception:
        return False


def run(
    duration: int,
    interval: int,
    message: str,
    mode: str = "auto",
    action: str = "type",
    keys: Optional[str] = None,
    no_enter: bool = False,
    stop_event: Optional[threading.Event] = None,
) -> int:
    if interval <= 0:
        print("Interval must be a positive integer.", file=sys.stderr)
        return 2
    if duration <= 0:
        print("Duration must be a positive integer.", file=sys.stderr)
        return 2

    chosen_mode = mode.lower().strip()
    if chosen_mode not in {"auto", "type", "print"}:
        print("--mode must be one of: auto, type, print", file=sys.stderr)
        return 2

    chosen_action = action.lower().strip()
    if chosen_action not in {"type", "press"}:
        print("--action must be one of: type, press", file=sys.stderr)
        return 2

    pya = _try_import_pyautogui() if chosen_mode in ("auto", "type") else None
    can_control_keyboard = pya is not None and chosen_mode in ("auto", "type")

    start = time.monotonic()
    end = start + duration

    mode_label = "type" if can_control_keyboard else "print"
    print(
        f"Starting work_flow at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"duration={duration}s, interval={interval}s, mode={mode_label}, action={chosen_action}"
    )
    if chosen_mode == "type" and pya is None:
        print("pyautogui not available; falling back to print mode.")

    # Schedule loop on fixed cadence to avoid drift
    next_fire = start

    try:
        while True:
            # Allow cooperative stop
            if stop_event is not None and stop_event.is_set():
                print("Stopped by user (Stop button). Exiting early.")
                return 0

            now = time.monotonic()
            if now >= end:
                break

            # Fire action if due
            if now >= next_fire:
                timestamp = datetime.now().strftime('%H:%M:%S')
                if chosen_action == "type":
                    if can_control_keyboard and pya is not None:
                        ok = _type_message(pya, message, press_enter=not no_enter)
                        if not ok:
                            print(f"[{timestamp}] (fallback) {message}")
                            can_control_keyboard = False
                            pya = None
                    else:
                        # Printing what would be typed
                        suffix = "" if no_enter else " + Enter"
                        print(f"[{timestamp}] (would type) {message}{suffix}")
                else:  # press mode
                    keys_to_press = (keys or "enter").strip()
                    if can_control_keyboard and pya is not None:
                        ok = _press_keys(pya, keys_to_press)
                        if not ok:
                            print(f"[{timestamp}] (fallback would press) {keys_to_press}")
                            can_control_keyboard = False
                            pya = None
                    else:
                        print(f"[{timestamp}] (would press) {keys_to_press}")

                # Schedule next
                next_fire += interval

            # Sleep a bit to avoid busy-waiting while remaining responsive to stop
            if stop_event is not None:
                # Sleep up to 50ms or until stop_event is set
                stop_event.wait(0.05)
            else:
                time.sleep(0.05)

        print("Done. Exiting.")
        return 0
    except KeyboardInterrupt:
        print("Interrupted by user. Exiting early.")
        return 130


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Type text or press keys every N seconds for a set duration.")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION_SECONDS, help=f"Total run time in seconds (default: {DEFAULT_DURATION_SECONDS})")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS, help=f"Seconds between each action (default: {DEFAULT_INTERVAL_SECONDS})")
    parser.add_argument("--mode", type=str, default=DEFAULT_MODE, choices=["auto", "type", "print"], help="auto=try to control keyboard with pyautogui, else print; type=force keyboard control; print=console only")
    parser.add_argument("--action", type=str, default=DEFAULT_ACTION, choices=["type", "press"], help="type=enter text; press=simulate key press(es)")
    parser.add_argument("--message", type=str, default=DEFAULT_MESSAGE, help="Text to type when --action type is chosen")
    # --no-enter default comes from DEFAULT_NO_ENTER via set_defaults below
    parser.add_argument("--no-enter", action="store_true", help="Do not press Enter after typing text")
    parser.add_argument("--keys", type=str, default=DEFAULT_KEYS if DEFAULT_KEYS else "", help="Keys to press when --action press is chosen. Examples: 'enter', 'ctrl+s', 'down,enter'")
    parser.set_defaults(no_enter=DEFAULT_NO_ENTER)
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    sys.exit(
        run(
            duration=args.duration,
            interval=args.interval,
            message=args.message,
            mode=args.mode,
            action=args.action,
            keys=args.keys,
            no_enter=args.no_enter,
        )
    )
