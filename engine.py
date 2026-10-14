"""
Human Code Typer - Core Engine
Simulates ultra-realistic human typing dynamics for code:
- Gaussian jitter around base WPM
- Muscle-memory burst typing on code keywords and identifiers
- Natural thinking pauses at newlines, block ends, and punctuation
- Exact 100% faithful typing mode (zero typos / no spelling errors)
- Realistic QWERTY neighbor typos with human reaction latency and backspacing (optional)
- Smart adaptive indentation engine for modern IDEs (VS Code, LeetCode, Monaco, JetBrains)
- Thread-safe pause, resume, and emergency abort
"""

import time
import random
import threading
from enum import Enum
from typing import Callable, Optional, Dict, List
from pynput.keyboard import Controller, Key

# Adjacent keys on a standard US QWERTY physical keyboard
QWERTY_NEIGHBORS: Dict[str, str] = {
    'q': 'wa12', 'w': 'qase23', 'e': 'wsdr34', 'r': 'edft45', 't': 'rfgy56',
    'y': 'tghu67', 'u': 'yhji78', 'i': 'ujko89', 'o': 'iklp90', 'p': 'ol0-',
    'a': 'qwsz', 's': 'awedxz', 'd': 'serfcx', 'f': 'drtgvc', 'g': 'ftyhbv',
    'h': 'gyujnb', 'j': 'huikmn', 'k': 'jiolm', 'l': 'kop;',
    'z': 'asx', 'x': 'zsdc', 'c': 'xdfv', 'v': 'cfgb', 'b': 'vghn',
    'n': 'bhjm', 'm': 'njk,',
    '1': '2q', '2': '13qw', '3': '24we', '4': '35er', '5': '46rt',
    '6': '57ty', '7': '68yu', '8': '79ui', '9': '80io', '0': '9-op',
    '-': '0=', '=': '-[', '[': ']=', ']': '[\\',
    ';': 'lp\'', '\'': ';[', ',': 'm.k', '.': ',/l', '/': '.'
}

COMMON_CODE_KEYWORDS = {
    "def", "class", "return", "import", "from", "function", "const", "let",
    "var", "async", "await", "public", "private", "static", "void", "int",
    "string", "boolean", "if", "else", "elif", "for", "while", "break",
    "continue", "try", "catch", "finally", "except", "throw", "raise",
    "true", "false", "null", "None", "self", "this", "console", "print"
}


class IndentMode(Enum):
    SMART_IDE = "smart_ide"        # Adaptive auto-indent tracking (VS Code, LeetCode, Monaco, JetBrains)
    RAW = "raw"                    # Types all newlines and indentation spaces literally (Notepad/terminals)
    CLEAN_EXACT = "clean_exact"    # Shift+Home + Backspace line reset before typing


class TypingProfile:
    def __init__(
        self,
        name: str = "Exact As-Pasted (100% Faithful)",
        wpm: int = 75,
        jitter: float = 0.25,
        typo_rate: float = 0.0,  # Default 0.0 = zero spelling errors
        thinking_pause_newline: float = 0.35,
        thinking_pause_punct: float = 0.15,
        burst_multiplier: float = 1.35,
        indent_mode: IndentMode = IndentMode.SMART_IDE,
        countdown_sec: int = 5,
        tab_size: int = 4
    ):
        self.name = name
        self.wpm = wpm
        self.jitter = jitter
        self.typo_rate = typo_rate
        self.thinking_pause_newline = thinking_pause_newline
        self.thinking_pause_punct = thinking_pause_punct
        self.burst_multiplier = burst_multiplier
        self.indent_mode = indent_mode
        self.countdown_sec = countdown_sec
        self.tab_size = tab_size


PRESET_PROFILES = {
    "Exact As-Pasted (100% Faithful)": TypingProfile(
        name="Exact As-Pasted (100% Faithful)",
        wpm=75,
        jitter=0.25,
        typo_rate=0.0,
        thinking_pause_newline=0.35,
        thinking_pause_punct=0.15,
        burst_multiplier=1.35,
        indent_mode=IndentMode.SMART_IDE,
        countdown_sec=5
    ),
    "Natural Developer (No Errors)": TypingProfile(
        name="Natural Developer (No Errors)",
        wpm=65,
        jitter=0.35,
        typo_rate=0.0,
        thinking_pause_newline=0.45,
        thinking_pause_punct=0.20,
        burst_multiplier=1.30,
        indent_mode=IndentMode.SMART_IDE,
        countdown_sec=5
    ),
    "Senior Engineer (Fast & Clean)": TypingProfile(
        name="Senior Engineer (Fast & Clean)",
        wpm=85,
        jitter=0.25,
        typo_rate=0.0,
        thinking_pause_newline=0.35,
        thinking_pause_punct=0.15,
        burst_multiplier=1.45,
        indent_mode=IndentMode.SMART_IDE,
        countdown_sec=5
    ),
    "Speed Demon": TypingProfile(
        name="Speed Demon",
        wpm=125,
        jitter=0.20,
        typo_rate=0.0,
        thinking_pause_newline=0.18,
        thinking_pause_punct=0.08,
        burst_multiplier=1.60,
        indent_mode=IndentMode.SMART_IDE,
        countdown_sec=3
    ),
    "Live Coding Interview": TypingProfile(
        name="Live Coding Interview",
        wpm=55,
        jitter=0.40,
        typo_rate=0.0,
        thinking_pause_newline=0.70,
        thinking_pause_punct=0.25,
        burst_multiplier=1.20,
        indent_mode=IndentMode.SMART_IDE,
        countdown_sec=5
    ),
    "Realistic Typos & Fixes (Simulated Mistakes)": TypingProfile(
        name="Realistic Typos & Fixes (Simulated Mistakes)",
        wpm=65,
        jitter=0.35,
        typo_rate=0.025,
        thinking_pause_newline=0.50,
        thinking_pause_punct=0.22,
        burst_multiplier=1.30,
        indent_mode=IndentMode.SMART_IDE,
        countdown_sec=5
    )
}


class HumanTyperEngine:
    def __init__(self):
        self.keyboard = Controller()
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        self._typing_thread: Optional[threading.Thread] = None
        self._is_running = False
        self._is_paused = False

        # Callbacks
        self.on_progress: Optional[Callable[[int, int, str, float], None]] = None
        self.on_status: Optional[Callable[[str], None]] = None
        self.on_finished: Optional[Callable[[], None]] = None
        self.on_stopped: Optional[Callable[[], None]] = None
        self.on_virtual_char: Optional[Callable[[str], None]] = None
        self.on_virtual_backspace: Optional[Callable[[], None]] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def calculate_base_delay(self, wpm: int) -> float:
        """Standard keystroke delay: 1 WPM = 5 chars/min"""
        chars_per_sec = (wpm * 5.0) / 60.0
        return 1.0 / max(chars_per_sec, 1.0)

    def get_typo_char(self, char: str) -> Optional[str]:
        """Returns a plausible adjacent QWERTY key error."""
        lower_char = char.lower()
        if lower_char in QWERTY_NEIGHBORS:
            candidates = QWERTY_NEIGHBORS[lower_char]
            typo = random.choice(candidates)
            return typo.upper() if char.isupper() else typo
        return None

    def _sleep_interruptible(self, duration: float) -> bool:
        """Sleep in small chunks so stop/pause can interrupt immediately."""
        step = 0.02
        elapsed = 0.0
        while elapsed < duration:
            if self._stop_event.is_set():
                return False
            # Wait if paused
            while not self._pause_event.is_set():
                if self._stop_event.is_set():
                    return False
                time.sleep(0.05)
            time.sleep(min(step, duration - elapsed))
            elapsed += step
        return True

    def start_typing(
        self,
        code_text: str,
        profile: TypingProfile,
        virtual_mode: bool = False
    ):
        """Starts human typing in a dedicated worker thread."""
        if self._is_running:
            return

        self._stop_event.clear()
        self._pause_event.set()
        self._is_running = True
        self._is_paused = False

        self._typing_thread = threading.Thread(
            target=self._run_typing_loop,
            args=(code_text, profile, virtual_mode),
            daemon=True
        )
        self._typing_thread.start()

    def pause(self):
        """Pauses typing execution."""
        if self._is_running and not self._is_paused:
            self._pause_event.clear()
            self._is_paused = True
            if self.on_status:
                self.on_status("Paused (Press F7 or click Resume to continue)")

    def resume(self):
        """Resumes paused typing execution."""
        if self._is_running and self._is_paused:
            self._pause_event.set()
            self._is_paused = False
            if self.on_status:
                self.on_status("Typing in progress...")

    def toggle_pause(self):
        if self._is_paused:
            self.resume()
        else:
            self.pause()

    def stop(self):
        """Immediately aborts typing."""
        if self._is_running:
            self._stop_event.set()
            self._pause_event.set()  # Unblock if waiting
            self._is_running = False
            self._is_paused = False
            if self.on_status:
                self.on_status("Stopped by user")
            if self.on_stopped:
                self.on_stopped()

    def _emit_char(self, char: str, virtual_mode: bool):
        if virtual_mode:
            if self.on_virtual_char:
                self.on_virtual_char(char)
        else:
            if char == '\n':
                self.keyboard.press(Key.enter)
                self.keyboard.release(Key.enter)
            elif char == '\t':
                self.keyboard.press(Key.tab)
                self.keyboard.release(Key.tab)
            elif char == '\r':
                pass  # Ignore CR in Windows CRLF to prevent duplicate enters
            else:
                self.keyboard.type(char)

    def _emit_backspace(self, virtual_mode: bool):
        if virtual_mode:
            if self.on_virtual_backspace:
                self.on_virtual_backspace()
        else:
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)

    def _emit_dedent(self, levels: int = 1, virtual_mode: bool = False):
        """
        Outdents in modern code editors using Shift+Tab.
        Shift+Tab is completely safe: it dedents by 1 tab stop and NEVER deletes
        the newline above even if the cursor is at column 0.
        """
        if virtual_mode:
            return
        for _ in range(levels):
            self.keyboard.press(Key.shift)
            self.keyboard.press(Key.tab)
            self.keyboard.release(Key.tab)
            self.keyboard.release(Key.shift)
            time.sleep(0.025)

    def _clean_auto_indent(self, virtual_mode: bool):
        """Safely cleans any auto-inserted indentation after Enter in clean_exact mode."""
        if not virtual_mode:
            # Home twice ensures cursor is at column 0 in VS Code and other editors
            self.keyboard.press(Key.home)
            self.keyboard.release(Key.home)
            time.sleep(0.01)
            self.keyboard.press(Key.home)
            self.keyboard.release(Key.home)
            time.sleep(0.01)
            # Select auto-indented whitespace
            self.keyboard.press(Key.shift)
            self.keyboard.press(Key.end)
            self.keyboard.release(Key.end)
            self.keyboard.release(Key.shift)
            time.sleep(0.015)
            # Delete selected whitespace (clears selection without deleting newline)
            self.keyboard.press(Key.backspace)
            self.keyboard.release(Key.backspace)
            time.sleep(0.015)

    def _normalize_leading_whitespace(self, line: str, tab_size: int = 4) -> str:
        """Converts leading tabs into spaces to prevent browser tab focus shifts."""
        idx = 0
        while idx < len(line) and line[idx] in (' ', '\t'):
            idx += 1
        leading_ws = line[:idx]
        content = line[idx:]
        expanded_ws = leading_ws.replace('\t', ' ' * tab_size)
        return expanded_ws + content

    def _line_opens_block(self, line_content: str) -> bool:
        """Detects if a line opens an indented block in Python, JS, C, Java, etc."""
        s = line_content.strip()
        if not s:
            return False
        # Avoid comments ending with colon (e.g., # Note:)
        if s.startswith('#') or s.startswith('//') or s.startswith('/*'):
            return False
        return s.endswith(':') or s.endswith('{') or s.endswith('(')

    def _run_typing_loop(
        self,
        code_text: str,
        profile: TypingProfile,
        virtual_mode: bool
    ):
        try:
            # Normalize line breaks
            normalized_code = code_text.replace('\r\n', '\n').replace('\r', '\n')
            total_chars = len(normalized_code)
            if total_chars == 0:
                if self.on_status:
                    self.on_status("Ready (No text to type)")
                return

            # Countdown phase (if not virtual test mode)
            if not virtual_mode and profile.countdown_sec > 0:
                for c in range(profile.countdown_sec, 0, -1):
                    if self._stop_event.is_set():
                        return
                    if self.on_status:
                        self.on_status(f"Starting in {c}s... Switch to your target window now!")
                    if not self._sleep_interruptible(1.0):
                        return

            if self.on_status:
                self.on_status("Typing code faithfully... (Press F8 or Esc to Stop)")

            base_delay = self.calculate_base_delay(profile.wpm)
            chars_typed = 0
            start_time = time.time()
            tab_size = getattr(profile, 'tab_size', 4)

            # Editor indent state tracker (starts at 0)
            current_editor_indent = 0

            lines = normalized_code.splitlines(keepends=True)

            for line_idx, raw_line in enumerate(lines):
                if self._stop_event.is_set():
                    break

                # Normalize leading tabs to consistent spaces
                line = self._normalize_leading_whitespace(raw_line, tab_size)
                has_newline = line.endswith('\n')
                line_content = line[:-1] if has_newline else line

                # Measure leading indentation and stripped content
                stripped_content = line_content.lstrip(' ')
                leading_spaces = len(line_content) - len(stripped_content)
                is_empty_or_whitespace = (len(stripped_content) == 0)

                # Indentation handling
                if line_idx == 0:
                    # Line 0 starts at column 0 in target window; type any leading spaces
                    if leading_spaces > 0:
                        for _ in range(leading_spaces):
                            self._emit_char(' ', virtual_mode)
                            chars_typed += 1
                            if not virtual_mode:
                                time.sleep(0.008)
                        current_editor_indent = leading_spaces
                else:
                    # For lines after the first line (line_idx > 0)
                    if virtual_mode:
                        # In-app sandbox doesn't auto-indent; type all leading spaces literally
                        if leading_spaces > 0:
                            for _ in range(leading_spaces):
                                self._emit_char(' ', virtual_mode)
                                chars_typed += 1
                    elif profile.indent_mode == IndentMode.SMART_IDE:
                        if not is_empty_or_whitespace:
                            if leading_spaces > current_editor_indent:
                                # Editor has fewer spaces than target: type missing spaces
                                extra_spaces = leading_spaces - current_editor_indent
                                for _ in range(extra_spaces):
                                    self._emit_char(' ', virtual_mode)
                                    chars_typed += 1
                                    time.sleep(0.008)
                            elif leading_spaces < current_editor_indent:
                                # Editor is indented further: dedent back to target
                                dedent_diff = current_editor_indent - leading_spaces
                                levels = max(1, dedent_diff // tab_size)
                                self._emit_dedent(levels, virtual_mode)
                                current_editor_indent = leading_spaces
                            # If leading_spaces == current_editor_indent:
                            # Editor is ALREADY at exact indent! 0 spaces typed!
                    elif profile.indent_mode == IndentMode.RAW:
                        # Raw literal mode: type all leading spaces explicitly
                        if leading_spaces > 0:
                            for _ in range(leading_spaces):
                                self._emit_char(' ', virtual_mode)
                                chars_typed += 1
                                time.sleep(0.008)
                    elif profile.indent_mode == IndentMode.CLEAN_EXACT:
                        self._clean_auto_indent(virtual_mode)
                        if leading_spaces > 0:
                            for _ in range(leading_spaces):
                                self._emit_char(' ', virtual_mode)
                                chars_typed += 1
                                time.sleep(0.008)

                # Type stripped content character by character
                content_len = len(stripped_content)
                char_idx = 0

                while char_idx < content_len:
                    if self._stop_event.is_set():
                        break

                    char = stripped_content[char_idx]

                    # 1. Typo simulation (Only active if typo_rate > 0)
                    if profile.typo_rate > 0.0 and char.isalnum() and random.random() < profile.typo_rate:
                        typo_char = self.get_typo_char(char)
                        if typo_char:
                            # Type mistyped key
                            self._emit_char(typo_char, virtual_mode)
                            typo_delay = max(0.04, random.gauss(base_delay * 0.9, base_delay * 0.2))
                            self._sleep_interruptible(typo_delay)

                            # Reaction pause
                            reaction_time = random.uniform(0.14, 0.30)
                            self._sleep_interruptible(reaction_time)

                            # Backspace correction
                            self._emit_backspace(virtual_mode)
                            self._sleep_interruptible(random.uniform(0.08, 0.16))

                    # 2. Type actual correct character
                    self._emit_char(char, virtual_mode)
                    chars_typed += 1
                    char_idx += 1

                    # 3. Dynamic human delay
                    # Check for keyword burst speedup
                    current_word = ""
                    w_start = max(0, char_idx - 1)
                    while w_start > 0 and stripped_content[w_start - 1].isalnum():
                        w_start -= 1
                    w_end = char_idx
                    while w_end < content_len and stripped_content[w_end].isalnum():
                        w_end += 1
                    token = stripped_content[w_start:w_end]

                    is_burst = (token in COMMON_CODE_KEYWORDS) or (len(token) > 4 and token.isalnum())
                    effective_wpm = profile.wpm * (profile.burst_multiplier if is_burst else 1.0)
                    char_base = self.calculate_base_delay(int(effective_wpm))

                    # Gaussian jitter around base delay
                    sigma = char_base * profile.jitter
                    delay = max(0.012, random.gauss(char_base, sigma))

                    # Punctuation pauses
                    if char in (',', ';', ':', '{', '}', ')'):
                        punct_pause = random.gauss(
                            profile.thinking_pause_punct,
                            profile.thinking_pause_punct * 0.3
                        )
                        delay += max(0.03, punct_pause)
                    elif char == ' ':
                        delay *= random.uniform(0.9, 1.2)

                    # Update progress
                    elapsed = max(0.001, time.time() - start_time)
                    current_wpm = (chars_typed / 5.0) / (elapsed / 60.0)

                    if self.on_progress:
                        self.on_progress(chars_typed, total_chars, char, current_wpm)

                    if not self._sleep_interruptible(delay):
                        break

                # 4. Handle newline at end of line
                if has_newline:
                    if self._stop_event.is_set():
                        break

                    # Detect if line opens an indented block
                    opens_block = self._line_opens_block(stripped_content)

                    if profile.indent_mode == IndentMode.SMART_IDE and not virtual_mode:
                        if is_empty_or_whitespace:
                            # Empty lines preserve indent state
                            pass
                        elif opens_block:
                            current_editor_indent = leading_spaces + tab_size
                        else:
                            current_editor_indent = leading_spaces

                    # Emit newline
                    self._emit_char('\n', virtual_mode)
                    chars_typed += 1

                    # Thinking pause after completing a line of code
                    newline_pause = random.gauss(
                        profile.thinking_pause_newline,
                        profile.thinking_pause_newline * 0.25
                    )
                    delay = max(0.08, newline_pause)

                    elapsed = max(0.001, time.time() - start_time)
                    current_wpm = (chars_typed / 5.0) / (elapsed / 60.0)
                    if self.on_progress:
                        self.on_progress(chars_typed, total_chars, '\n', current_wpm)

                    if not self._sleep_interruptible(delay):
                        break

            if not self._stop_event.is_set():
                if self.on_status:
                    self.on_status("Finished! All code typed faithfully with exact indentation.")
                if self.on_finished:
                    self.on_finished()

        finally:
            self._is_running = False
            self._is_paused = False
