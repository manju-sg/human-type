"""
Human Code Typer - CLI
Allows typing code directly from terminal, file, or clipboard into any active window.

Usage examples:
  python -m human_typer.cli --clipboard --wpm 80
  python -m human_typer.cli --file solution.py --preset "Senior Engineer"
  python -m human_typer.cli --file script.js --countdown 8 --typos 2.0
"""

import sys
import time
import argparse
from typing import Optional
import pyperclip
from pynput import keyboard as pynput_kb

from human_typer.engine import (
    HumanTyperEngine,
    TypingProfile,
    IndentMode,
    PRESET_PROFILES
)


def main():
    parser = argparse.ArgumentParser(
        description="Human Code Typer - Type code realistically like a human into any window."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-c", "--clipboard",
        action="store_true",
        help="Type text currently in the system clipboard"
    )
    group.add_argument(
        "-f", "--file",
        type=str,
        help="Path to code file to type"
    )
    group.add_argument(
        "-t", "--text",
        type=str,
        help="Raw text string to type"
    )

    parser.add_argument(
        "-p", "--preset",
        type=str,
        choices=list(PRESET_PROFILES.keys()),
        default="Exact As-Pasted (100% Faithful)",
        help="Typing preset profile (default: 'Exact As-Pasted (100% Faithful)')"
    )
    parser.add_argument(
        "--wpm",
        type=int,
        default=None,
        help="Typing speed in Words Per Minute (e.g. 75)"
    )
    parser.add_argument(
        "--typos",
        type=float,
        default=None,
        help="Typo rate percentage (e.g. 0.0 for exact, 2.5 for 2.5%%)"
    )
    parser.add_argument(
        "--countdown",
        type=int,
        default=None,
        help="Seconds to wait before typing begins (default: 5)"
    )
    parser.add_argument(
        "--indent-mode",
        type=str,
        choices=["smart_ide", "raw", "clean_exact"],
        default="smart_ide",
        help="Indentation mode (default: smart_ide for VS Code / LeetCode / IDEs)"
    )

    args = parser.parse_args()

    # Obtain code text
    code_text = ""
    if args.clipboard:
        code_text = pyperclip.paste()
        if not code_text:
            print("[Error] Clipboard is empty!")
            sys.exit(1)
        print(f"[Info] Loaded {len(code_text)} characters from clipboard.")
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fp:
                code_text = fp.read()
            print(f"[Info] Loaded {len(code_text)} characters from '{args.file}'.")
        except Exception as e:
            print(f"[Error] Failed to read file: {e}")
            sys.exit(1)
    elif args.text:
        code_text = args.text

    # Build profile
    base_profile = PRESET_PROFILES[args.preset]
    profile = TypingProfile(
        name=base_profile.name,
        wpm=args.wpm if args.wpm is not None else base_profile.wpm,
        jitter=base_profile.jitter,
        typo_rate=(args.typos / 100.0) if args.typos is not None else base_profile.typo_rate,
        thinking_pause_newline=base_profile.thinking_pause_newline,
        thinking_pause_punct=base_profile.thinking_pause_punct,
        burst_multiplier=base_profile.burst_multiplier,
        indent_mode=IndentMode(args.indent_mode),
        countdown_sec=args.countdown if args.countdown is not None else base_profile.countdown_sec
    )

    engine = HumanTyperEngine()

    def on_status(msg):
        print(f"\r[Status] {msg}", flush=True)

    def on_progress(typed, total, char, wpm):
        pct = int((typed / max(total, 1)) * 100)
        sys.stdout.write(f"\r[Progress] {typed}/{total} chars ({pct}%) | Speed: {int(wpm)} WPM   ")
        sys.stdout.flush()

    engine.on_status = on_status
    engine.on_progress = on_progress

    # Setup global hotkey for emergency stop
    def on_press(key):
        if key == pynput_kb.Key.f8 or key == pynput_kb.Key.esc:
            print("\n[Hotkey] Emergency stop triggered!")
            engine.stop()

    hotkey_listener = pynput_kb.Listener(on_press=on_press)
    hotkey_listener.daemon = True
    hotkey_listener.start()

    print("=" * 60)
    print(f" Human Code Typer CLI | Preset: {profile.name}")
    print(f" Target Speed: {profile.wpm} WPM | Typo Rate: {profile.typo_rate * 100:.1f}%")
    print(f" Switch window delay: {profile.countdown_sec}s | Indent mode: {profile.indent_mode.value}")
    print(" Emergency Stop: Press F8 or ESC at any time to abort")
    print("=" * 60)

    engine.start_typing(code_text, profile, virtual_mode=False)

    while engine.is_running:
        time.sleep(0.1)

    print("\n[Done] Finished typing.")


if __name__ == "__main__":
    main()
