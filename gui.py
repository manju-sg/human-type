"""
Human Code Typer - Modern Desktop GUI
Features:
- Sleek CustomTkinter Dark Mode Interface
- Live Code Input with sample presets (Python, JS, C++, SQL)
- Instant In-App Test Sandbox (Preview before typing into external apps)
- Preset Profiles (Casual Dev, Senior Eng, Speed Demon, Interview Mode, Flawless)
- Sliders for WPM, Jitter, Typo Rate, Thinking Pauses, Countdown
- Smart Indentation Modes for VS Code, LeetCode, JetBrains, Notepad
- Global Hotkeys: F8 / Esc to Emergency Stop, F7 to Pause / Resume
- Live Progress Bar and Keystroke / WPM Telemetry
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pynput import keyboard as pynput_kb

from human_typer.engine import (
    HumanTyperEngine,
    TypingProfile,
    IndentMode,
    PRESET_PROFILES
)

# Set appearance theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

SAMPLE_SNIPPETS = {
    "Python (Binary Search)": '''def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# Test search
nums = [1, 3, 5, 7, 9, 11]
print("Found index:", binary_search(nums, 7))''',

    "JavaScript (Async Fetch)": '''async function fetchUserProfile(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("User data loaded:", data);
        return data;
    } catch (err) {
        console.error("Failed to load user:", err);
        return null;
    }
}''',

    "C++ (Fast Two-Sum)": '''#include <iostream>
#include <vector>
#include <unordered_map>

std::vector<int> twoSum(const std::vector<int>& nums, int target) {
    std::unordered_map<int, int> seen;
    for (int i = 0; i < nums.size(); ++i) {
        int complement = target - nums[i];
        if (seen.count(complement)) {
            return {seen[complement], i};
        }
        seen[nums[i]] = i;
    }
    return {};
}'''
}


class HumanTyperApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Human Code Typer")
        self.geometry("1100x720")
        self.minsize(980, 640)

        # Engine
        self.engine = HumanTyperEngine()
        self.engine.on_progress = self._on_engine_progress
        self.engine.on_status = self._on_engine_status
        self.engine.on_finished = self._on_engine_finished
        self.engine.on_stopped = self._on_engine_stopped
        self.engine.on_virtual_char = self._on_virtual_char
        self.engine.on_virtual_backspace = self._on_virtual_backspace

        self.current_profile = TypingProfile()
        self._is_virtual_test = False

        # Setup GUI Components
        self._build_ui()
        self._setup_global_hotkeys()
        self._load_preset("Exact As-Pasted (100% Faithful)")

        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _setup_global_hotkeys(self):
        """Global listener for F8 / Esc (Stop) and F7 (Pause/Resume)."""
        def on_press(key):
            try:
                if key == pynput_kb.Key.f8 or key == pynput_kb.Key.esc:
                    if self.engine.is_running:
                        self.after(0, self._btn_stop_clicked)
                elif key == pynput_kb.Key.f7:
                    if self.engine.is_running:
                        self.after(0, self._btn_pause_clicked)
            except Exception:
                pass

        self.hotkey_listener = pynput_kb.Listener(on_press=on_press)
        self.hotkey_listener.daemon = True
        self.hotkey_listener.start()

    def _build_ui(self):
        # Configure Grid layout (2 columns: Editor area 65%, Controls 35%)
        self.grid_columnconfigure(0, weight=6)
        self.grid_columnconfigure(1, weight=4)
        self.grid_rowconfigure(1, weight=1)

        # 1. Header Bar
        self.header_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#18181b")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=0, pady=(0, 6))

        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=16, pady=10)

        self.lbl_title = ctk.CTkLabel(
            title_box,
            text="⌨️ Human Code Typer",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#f4f4f5"
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_subtitle = ctk.CTkLabel(
            title_box,
            text="Simulates realistic human cadence with 100% faithful spelling and smart IDE indentation",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#a1a1aa"
        )
        self.lbl_subtitle.pack(anchor="w")

        # Status badge pill
        self.status_badge = ctk.CTkLabel(
            self.header_frame,
            text="● Ready",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color="#27272a",
            text_color="#10b981",
            corner_radius=12,
            padx=14,
            pady=4
        )
        self.status_badge.pack(side="right", padx=16, pady=10)

        # 2. Left Column: Code Editor & In-App Preview Sandbox
        self.left_frame = ctk.CTkFrame(self, fg_color="#1e1e24", corner_radius=10)
        self.left_frame.grid(row=1, column=0, sticky="nsew", padx=(14, 6), pady=(0, 10))
        self.left_frame.grid_rowconfigure(1, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)

        # Tabview for Code Input vs In-App Preview Sandbox
        self.tabview = ctk.CTkTabview(self.left_frame, fg_color="#18181b")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_input = self.tabview.add("Code Input")
        self.tab_preview = self.tabview.add("Test Sandbox (Preview In-App)")

        # --- Tab 1: Code Input ---
        toolbar = ctk.CTkFrame(self.tab_input, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 6))

        lbl_input_hint = ctk.CTkLabel(
            toolbar,
            text="Paste your code below:",
            font=ctk.CTkFont(weight="bold", size=13),
            text_color="#e4e4e7"
        )
        lbl_input_hint.pack(side="left")

        # Sample snippet dropdown
        self.sample_dropdown = ctk.CTkOptionMenu(
            toolbar,
            values=["Load Sample..."] + list(SAMPLE_SNIPPETS.keys()),
            command=self._on_sample_selected,
            width=160,
            height=28,
            font=ctk.CTkFont(size=12)
        )
        self.sample_dropdown.pack(side="right", padx=(6, 0))

        btn_paste = ctk.CTkButton(
            toolbar,
            text="📋 Paste Clipboard",
            width=110,
            height=28,
            command=self._paste_clipboard,
            font=ctk.CTkFont(size=12)
        )
        btn_paste.pack(side="right", padx=4)

        btn_clear = ctk.CTkButton(
            toolbar,
            text="✕ Clear",
            width=65,
            height=28,
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=self._clear_input,
            font=ctk.CTkFont(size=12)
        )
        btn_clear.pack(side="right", padx=4)

        self.txt_code = ctk.CTkTextbox(
            self.tab_input,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="#121215",
            text_color="#38bdf8",
            wrap="none",
            undo=True
        )
        self.txt_code.pack(fill="both", expand=True, pady=(0, 6))
        self.txt_code.insert("1.0", SAMPLE_SNIPPETS["Python (Binary Search)"])
        self.txt_code.bind("<KeyRelease>", self._update_stats_label)

        self.lbl_stats = ctk.CTkLabel(
            self.tab_input,
            text="Characters: 0 | Lines: 0",
            font=ctk.CTkFont(size=11),
            text_color="#71717a"
        )
        self.lbl_stats.pack(anchor="w")

        # --- Tab 2: Test Sandbox (Preview In-App) ---
        preview_bar = ctk.CTkFrame(self.tab_preview, fg_color="transparent")
        preview_bar.pack(fill="x", pady=(0, 6))

        lbl_sandbox_info = ctk.CTkLabel(
            preview_bar,
            text="Test typing cadence and typos safely in-app before targeting external windows:",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        lbl_sandbox_info.pack(side="left")

        btn_clear_sandbox = ctk.CTkButton(
            preview_bar,
            text="Clear Sandbox",
            width=90,
            height=26,
            fg_color="#3f3f46",
            hover_color="#52525b",
            command=lambda: self.txt_sandbox.delete("1.0", "end"),
            font=ctk.CTkFont(size=11)
        )
        btn_clear_sandbox.pack(side="right")

        self.txt_sandbox = ctk.CTkTextbox(
            self.tab_preview,
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="#121215",
            text_color="#a3e635",
            wrap="none"
        )
        self.txt_sandbox.pack(fill="both", expand=True)

        # 3. Right Column: Controls, Presets & Sliders
        self.right_frame = ctk.CTkScrollableFrame(self, fg_color="#1e1e24", corner_radius=10)
        self.right_frame.grid(row=1, column=1, sticky="nsew", padx=(6, 14), pady=(0, 10))

        # --- Presets Section ---
        lbl_preset_heading = ctk.CTkLabel(
            self.right_frame,
            text="Typing Presets",
            font=ctk.CTkFont(weight="bold", size=14),
            text_color="#f4f4f5"
        )
        lbl_preset_heading.pack(anchor="w", padx=6, pady=(4, 2))

        self.preset_dropdown = ctk.CTkOptionMenu(
            self.right_frame,
            values=list(PRESET_PROFILES.keys()),
            command=self._on_preset_dropdown_changed,
            height=32
        )
        self.preset_dropdown.pack(fill="x", padx=6, pady=(0, 12))

        # --- Sliders & Config ---
        # 1. Typing Speed (WPM)
        self.lbl_wpm = ctk.CTkLabel(
            self.right_frame,
            text="Typing Speed: 70 WPM (~350 CPM)",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_wpm.pack(anchor="w", padx=6)

        self.slider_wpm = ctk.CTkSlider(
            self.right_frame,
            from_=30,
            to=180,
            number_of_steps=30,
            command=self._on_wpm_slider
        )
        self.slider_wpm.pack(fill="x", padx=6, pady=(2, 10))

        # 2. Speed Jitter (Random Variance)
        self.lbl_jitter = ctk.CTkLabel(
            self.right_frame,
            text="Cadence Variance / Jitter: 35%",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_jitter.pack(anchor="w", padx=6)

        self.slider_jitter = ctk.CTkSlider(
            self.right_frame,
            from_=0.0,
            to=0.8,
            command=self._on_jitter_slider
        )
        self.slider_jitter.pack(fill="x", padx=6, pady=(2, 10))

        # 3. Exact Mode & Typo Simulation Rate
        self.switch_exact_mode = ctk.CTkSwitch(
            self.right_frame,
            text="Exact Typing (Zero Typos / 100% Faithful)",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._on_exact_mode_toggled
        )
        self.switch_exact_mode.pack(anchor="w", padx=6, pady=(2, 6))
        self.switch_exact_mode.select()

        self.lbl_typo = ctk.CTkLabel(
            self.right_frame,
            text="Typo Rate: 0.0% (Exact Spelling Guarantee)",
            font=ctk.CTkFont(size=11)
        )
        self.lbl_typo.pack(anchor="w", padx=6)

        self.slider_typo = ctk.CTkSlider(
            self.right_frame,
            from_=0.0,
            to=0.08,
            command=self._on_typo_slider
        )
        self.slider_typo.pack(fill="x", padx=6, pady=(2, 10))
        self.slider_typo.set(0.0)
        self.slider_typo.configure(state="disabled")

        # 4. Thinking Pause at Newlines
        self.lbl_pause_nl = ctk.CTkLabel(
            self.right_frame,
            text="Thinking Pause at Newlines: 0.35s",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.lbl_pause_nl.pack(anchor="w", padx=6)

        self.slider_pause_nl = ctk.CTkSlider(
            self.right_frame,
            from_=0.05,
            to=1.5,
            command=self._on_pause_nl_slider
        )
        self.slider_pause_nl.pack(fill="x", padx=6, pady=(2, 10))

        # 5. Smart Indentation Mode
        lbl_indent = ctk.CTkLabel(
            self.right_frame,
            text="IDE Indentation Handling:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_indent.pack(anchor="w", padx=6)

        self.indent_mode_menu = ctk.CTkOptionMenu(
            self.right_frame,
            values=[
                "Smart Auto-Indent (VS Code / LeetCode / IDEs)",
                "Literal / Raw (Notepad / Terminals / Plain Text)",
                "Clean Line Reset (Shift+Home+BS)"
            ],
            command=self._on_indent_mode_changed,
            height=30
        )
        self.indent_mode_menu.pack(fill="x", padx=6, pady=(2, 10))

        # 6. Countdown Before Typing
        lbl_countdown = ctk.CTkLabel(
            self.right_frame,
            text="Countdown to Switch Window:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_countdown.pack(anchor="w", padx=6)

        self.countdown_menu = ctk.CTkSegmentedButton(
            self.right_frame,
            values=["3 sec", "5 sec", "8 sec", "10 sec"],
            command=self._on_countdown_changed
        )
        self.countdown_menu.set("5 sec")
        self.countdown_menu.pack(fill="x", padx=6, pady=(2, 14))

        # 7. Hotkey Helper Box
        hotkey_box = ctk.CTkFrame(self.right_frame, fg_color="#18181b", corner_radius=6)
        hotkey_box.pack(fill="x", padx=6, pady=(0, 14))

        lbl_hk_title = ctk.CTkLabel(
            hotkey_box,
            text="⚡ Global Hotkeys (Works anywhere):",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e4e4e7"
        )
        lbl_hk_title.pack(anchor="w", padx=8, pady=(6, 2))

        lbl_hk_body = ctk.CTkLabel(
            hotkey_box,
            text="• F8 or Esc  : Emergency Stop (Killswitch)\n• F7          : Pause / Resume Typing",
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color="#38bdf8",
            justify="left"
        )
        lbl_hk_body.pack(anchor="w", padx=8, pady=(0, 6))

        # 8. Action Buttons
        self.btn_start = ctk.CTkButton(
            self.right_frame,
            text="▶ Start Auto-Typing (Target Window)",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=40,
            command=self._btn_start_clicked
        )
        self.btn_start.pack(fill="x", padx=6, pady=(0, 6))

        btn_row = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=6, pady=(0, 6))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        self.btn_test_app = ctk.CTkButton(
            btn_row,
            text="⚡ Test in Sandbox",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#3b82f6",
            hover_color="#2563eb",
            height=34,
            command=self._btn_test_sandbox_clicked
        )
        self.btn_test_app.grid(row=0, column=0, sticky="ew", padx=(0, 3))

        self.btn_pause = ctk.CTkButton(
            btn_row,
            text="⏸ Pause (F7)",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#d97706",
            hover_color="#b45309",
            height=34,
            state="disabled",
            command=self._btn_pause_clicked
        )
        self.btn_pause.grid(row=0, column=1, sticky="ew", padx=(3, 0))

        self.btn_stop = ctk.CTkButton(
            self.right_frame,
            text="⏹ Emergency Stop (F8 / Esc)",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            height=36,
            state="disabled",
            command=self._btn_stop_clicked
        )
        self.btn_stop.pack(fill="x", padx=6, pady=(0, 8))

        # 4. Bottom Footer: Progress Bar & Telemetry
        self.footer_frame = ctk.CTkFrame(self, fg_color="#18181b", corner_radius=0, height=44)
        self.footer_frame.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.progress_bar = ctk.CTkProgressBar(self.footer_frame, height=8, corner_radius=4)
        self.progress_bar.pack(fill="x", padx=16, pady=(6, 2))
        self.progress_bar.set(0.0)

        info_row = ctk.CTkFrame(self.footer_frame, fg_color="transparent")
        info_row.pack(fill="x", padx=16, pady=(0, 6))

        self.lbl_progress_status = ctk.CTkLabel(
            info_row,
            text="Ready to type",
            font=ctk.CTkFont(size=12),
            text_color="#a1a1aa"
        )
        self.lbl_progress_status.pack(side="left")

        self.lbl_telemetry = ctk.CTkLabel(
            info_row,
            text="0 / 0 chars (0%) | 0 WPM",
            font=ctk.CTkFont(size=12, family="Consolas"),
            text_color="#e4e4e7"
        )
        self.lbl_telemetry.pack(side="right")

        self._update_stats_label()

    # --- UI Event Handlers ---
    def _update_stats_label(self, event=None):
        text = self.txt_code.get("1.0", "end-1c")
        chars = len(text)
        lines = len(text.splitlines()) if text else 0
        self.lbl_stats.configure(text=f"Characters: {chars} | Lines: {lines}")

    def _paste_clipboard(self):
        try:
            clipboard_text = self.clipboard_get()
            self.txt_code.delete("1.0", "end")
            self.txt_code.insert("1.0", clipboard_text)
            self._update_stats_label()
        except Exception:
            messagebox.showinfo("Clipboard", "Clipboard is empty or contains non-text content.")

    def _clear_input(self):
        self.txt_code.delete("1.0", "end")
        self._update_stats_label()

    def _on_sample_selected(self, choice):
        if choice in SAMPLE_SNIPPETS:
            self.txt_code.delete("1.0", "end")
            self.txt_code.insert("1.0", SAMPLE_SNIPPETS[choice])
            self._update_stats_label()

    def _on_preset_dropdown_changed(self, preset_name):
        self._load_preset(preset_name)

    def _load_preset(self, preset_name):
        if preset_name in PRESET_PROFILES:
            p = PRESET_PROFILES[preset_name]
            self.current_profile = TypingProfile(
                name=p.name,
                wpm=p.wpm,
                jitter=p.jitter,
                typo_rate=p.typo_rate,
                thinking_pause_newline=p.thinking_pause_newline,
                thinking_pause_punct=p.thinking_pause_punct,
                burst_multiplier=p.burst_multiplier,
                indent_mode=p.indent_mode,
                countdown_sec=p.countdown_sec
            )
            # Update UI controls
            self.slider_wpm.set(p.wpm)
            self._on_wpm_slider(p.wpm)

            self.slider_jitter.set(p.jitter)
            self._on_jitter_slider(p.jitter)

            if p.typo_rate == 0.0:
                self.switch_exact_mode.select()
                self.slider_typo.set(0.0)
                self.slider_typo.configure(state="disabled")
                self.lbl_typo.configure(text="Typo Rate: 0.0% (Exact Spelling Guarantee)")
            else:
                self.switch_exact_mode.deselect()
                self.slider_typo.configure(state="normal")
                self.slider_typo.set(p.typo_rate)
                self._on_typo_slider(p.typo_rate)

            self.slider_pause_nl.set(p.thinking_pause_newline)
            self._on_pause_nl_slider(p.thinking_pause_newline)

            if p.indent_mode == IndentMode.SMART_IDE:
                self.indent_mode_menu.set("Smart Auto-Indent (VS Code / LeetCode / IDEs)")
            elif p.indent_mode == IndentMode.RAW:
                self.indent_mode_menu.set("Literal / Raw (Notepad / Terminals / Plain Text)")
            else:
                self.indent_mode_menu.set("Clean Line Reset (Shift+Home+BS)")

            self.countdown_menu.set(f"{p.countdown_sec} sec")

    def _on_exact_mode_toggled(self):
        if self.switch_exact_mode.get() == 1:
            self.current_profile.typo_rate = 0.0
            self.slider_typo.set(0.0)
            self.slider_typo.configure(state="disabled")
            self.lbl_typo.configure(text="Typo Rate: 0.0% (Exact Spelling Guarantee)")
        else:
            self.slider_typo.configure(state="normal")
            self.slider_typo.set(0.02)
            self._on_typo_slider(0.02)

    def _on_wpm_slider(self, val):
        wpm = int(val)
        self.current_profile.wpm = wpm
        self.lbl_wpm.configure(text=f"Typing Speed: {wpm} WPM (~{wpm * 5} CPM)")

    def _on_jitter_slider(self, val):
        jitter = float(val)
        self.current_profile.jitter = jitter
        self.lbl_jitter.configure(text=f"Cadence Variance / Jitter: {int(jitter * 100)}%")

    def _on_typo_slider(self, val):
        rate = float(val)
        self.current_profile.typo_rate = rate
        pct = round(rate * 100, 1)
        if rate == 0.0:
            self.lbl_typo.configure(text="Typo Rate: 0.0% (Exact Spelling Guarantee)")
        else:
            self.lbl_typo.configure(text=f"Realistic Typo Rate: {pct}% (Mistype + Backspace)")

    def _on_pause_nl_slider(self, val):
        pause = round(float(val), 2)
        self.current_profile.thinking_pause_newline = pause
        self.lbl_pause_nl.configure(text=f"Thinking Pause at Newlines: {pause:.2f}s")

    def _on_indent_mode_changed(self, choice):
        if "Smart Auto-Indent" in choice:
            self.current_profile.indent_mode = IndentMode.SMART_IDE
        elif "Literal / Raw" in choice:
            self.current_profile.indent_mode = IndentMode.RAW
        else:
            self.current_profile.indent_mode = IndentMode.CLEAN_EXACT

    def _on_countdown_changed(self, val):
        try:
            sec = int(val.split()[0])
            self.current_profile.countdown_sec = sec
        except Exception:
            pass

    # --- Actions: Start / Test / Pause / Stop ---
    def _btn_start_clicked(self):
        code = self.txt_code.get("1.0", "end-1c")
        if not code.strip():
            messagebox.showwarning("Empty Code", "Please paste or write some code first!")
            return

        self._is_virtual_test = False
        self._set_ui_state_typing()
        self.engine.start_typing(code, self.current_profile, virtual_mode=False)

    def _btn_test_sandbox_clicked(self):
        code = self.txt_code.get("1.0", "end-1c")
        if not code.strip():
            messagebox.showwarning("Empty Code", "Please paste or write some code first!")
            return

        # Switch to preview tab
        self.tabview.set("Test Sandbox (Preview In-App)")
        self.txt_sandbox.delete("1.0", "end")

        self._is_virtual_test = True
        self._set_ui_state_typing()

        # In virtual sandbox, skip the 5s window-switch countdown for speed
        sandbox_profile = TypingProfile(
            name=self.current_profile.name,
            wpm=self.current_profile.wpm,
            jitter=self.current_profile.jitter,
            typo_rate=self.current_profile.typo_rate,
            thinking_pause_newline=self.current_profile.thinking_pause_newline,
            thinking_pause_punct=self.current_profile.thinking_pause_punct,
            burst_multiplier=self.current_profile.burst_multiplier,
            indent_mode=self.current_profile.indent_mode,
            countdown_sec=0
        )
        self.engine.start_typing(code, sandbox_profile, virtual_mode=True)

    def _btn_pause_clicked(self):
        if self.engine.is_paused:
            self.engine.resume()
            self.btn_pause.configure(text="⏸ Pause (F7)", fg_color="#d97706")
        else:
            self.engine.pause()
            self.btn_pause.configure(text="▶ Resume (F7)", fg_color="#10b981")

    def _btn_stop_clicked(self):
        self.engine.stop()
        self._set_ui_state_idle()

    # --- Engine Callbacks ---
    def _on_engine_progress(self, chars_typed: int, total_chars: int, current_char: str, wpm: float):
        fraction = chars_typed / max(total_chars, 1)
        pct = int(fraction * 100)
        self.after(0, lambda: self._update_progress_ui(chars_typed, total_chars, pct, wpm))

    def _update_progress_ui(self, typed, total, pct, wpm):
        self.progress_bar.set(typed / max(total, 1))
        self.lbl_telemetry.configure(text=f"{typed} / {total} chars ({pct}%) | {int(wpm)} WPM")

    def _on_engine_status(self, status_msg: str):
        self.after(0, lambda: self._update_status_ui(status_msg))

    def _update_status_ui(self, status_msg):
        self.lbl_progress_status.configure(text=status_msg)
        if "Starting in" in status_msg:
            self.status_badge.configure(text="● Countdown", text_color="#f59e0b")
        elif "Typing" in status_msg:
            self.status_badge.configure(text="● Typing...", text_color="#38bdf8")
        elif "Paused" in status_msg:
            self.status_badge.configure(text="● Paused", text_color="#fbbf24")
        elif "Finished" in status_msg:
            self.status_badge.configure(text="● Done", text_color="#10b981")
            self._set_ui_state_idle()
        elif "Stopped" in status_msg:
            self.status_badge.configure(text="● Stopped", text_color="#ef4444")
            self._set_ui_state_idle()

    def _on_engine_finished(self):
        self.after(0, self._set_ui_state_idle)

    def _on_engine_stopped(self):
        self.after(0, self._set_ui_state_idle)

    def _on_virtual_char(self, char: str):
        self.after(0, lambda: self._insert_sandbox_char(char))

    def _insert_sandbox_char(self, char: str):
        self.txt_sandbox.insert("end", char)
        self.txt_sandbox.see("end")

    def _on_virtual_backspace(self):
        self.after(0, self._delete_sandbox_char)

    def _delete_sandbox_char(self):
        # Delete last character in sandbox
        idx = self.txt_sandbox.index("end-1c")
        if idx != "1.0":
            prev_idx = f"{idx}-1c"
            self.txt_sandbox.delete(prev_idx, idx)

    def _set_ui_state_typing(self):
        self.btn_start.configure(state="disabled")
        self.btn_test_app.configure(state="disabled")
        self.btn_pause.configure(state="normal", text="⏸ Pause (F7)", fg_color="#d97706")
        self.btn_stop.configure(state="normal")

    def _set_ui_state_idle(self):
        self.btn_start.configure(state="normal")
        self.btn_test_app.configure(state="normal")
        self.btn_pause.configure(state="disabled", text="⏸ Pause (F7)", fg_color="#d97706")
        self.btn_stop.configure(state="disabled")

    def _on_closing(self):
        self.engine.stop()
        if hasattr(self, 'hotkey_listener'):
            self.hotkey_listener.stop()
        self.destroy()


def main():
    app = HumanTyperApp()
    app.mainloop()


if __name__ == "__main__":
    main()
