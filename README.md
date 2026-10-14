# ⌨️ Human Code Typer

An intelligent code typing simulator designed to type code keystroke-by-keystroke into any active window (VS Code, Chrome/LeetCode, Notepad, terminal) or in-browser with ultra-realistic human cadence and dynamics.

---

## ✨ Features

- **Exact 100% Faithful Typing**: Types code exactly as pasted without spelling mistakes, typos, or syntax errors.
- **Smart IDE Indentation Engine**: Solves the common "double indentation" and "dedent" bugs in modern editors (VS Code, JetBrains, LeetCode, CodePen) by tracking block opening (`:`, `{`), calculating indentation deltas, and dedenting smoothly with `Shift+Tab`.
- **Realistic Human Cadence**: Gaussian delay distribution around your desired WPM (Words Per Minute) instead of robotic fixed intervals.
- **Optional QWERTY Typos**: Can be enabled via slider when simulated human mistakes and self-corrections are desired.
- **Muscle-Memory Keyword Bursts**: Naturally accelerates (1.3x–1.6x) over familiar keywords (`def`, `return`, `function`, `class`, `import`, `const`, `console.log`).
- **Thinking Pauses**: Introduces natural micro-pauses at line breaks and syntax transitions (after commas, semicolons, and brackets).
- **Safety Killswitch & Controls**:
  - `F8` or `Esc`: Emergency Stop (immediately terminates typing).
  - `F7`: Pause / Resume.
  - Configurable countdown timer (3s, 5s, 8s, 10s) to give you time to switch to your destination window.
- **In-App Test Sandbox**: Preview and test your typing speed and exact indentation inside the app before targeting external windows.
- **Audio Feedback**: Subtle synthesized mechanical keyboard click feedback.

---

## 🚀 Quick Start

### Option 1: Double-Click Launcher (Windows)
Double-click `run_human_typer.bat` in the project root.

### Option 2: Run with Python
```bash
python run_typer.py
```
or
```bash
python -m human_typer.gui
```

### Option 3: Command Line (CLI)
Type directly from your clipboard or a file:
```bash
# Type whatever is in your clipboard at 80 WPM with a 5s countdown:
python -m human_typer.cli --clipboard --wpm 80

# Type a Python file using the "Senior Engineer" profile:
python -m human_typer.cli --file solution.py --preset "Senior Engineer"

# Type with custom typo rate and countdown:
python -m human_typer.cli --file script.js --wpm 90 --typos 2.0 --countdown 8
```

### Option 4: Visual Web Simulator (Browser)
Open `human_typer/web_simulator/index.html` in Chrome or Edge to enjoy the web simulator with mechanical keyboard audio synthesis and live telemetry.

---

## 🎛️ Preset Profiles

| Preset | Speed (WPM) | Typo Rate | Thinking Pause | Indent Engine | Best For |
|---|---|---|---|---|---|
| **Exact As-Pasted** *(Default)* | 75 WPM | 0.0% | 0.35s | Smart IDE | 100% faithful typing without spelling or indentation errors |
| **Natural Developer** | 65 WPM | 0.0% | 0.45s | Smart IDE | Natural cadence, zero spelling mistakes |
| **Senior Engineer** | 85 WPM | 0.0% | 0.35s | Smart IDE | Clean, steady professional typing |
| **Speed Demon** | 125 WPM | 0.0% | 0.18s | Smart IDE | Fast screencasts & live coding demos |
| **Live Coding Interview** | 55 WPM | 0.0% | 0.70s | Smart IDE | Thoughtful interview cadence |
| **Realistic Typos & Fixes** | 65 WPM | 2.5% | 0.50s | Smart IDE | When you deliberately want human mistakes & self-corrections |

---

## ⌨️ Global Hotkeys

| Key | Action |
|---|---|
| `F8` or `Esc` | **Emergency Stop** (Aborts typing instantly) |
| `F7` | **Pause / Resume** |

---

## 📁 Project Structure

```
human_typer/
├── __init__.py           # Package exports
├── engine.py             # Human typing simulation engine & QWERTY model
├── gui.py                # Modern CustomTkinter dark-mode desktop app
├── cli.py                # Command-line interface
├── web_simulator/        # Interactive HTML5/JS simulator with mechanical sound
│   └── index.html
run_typer.py              # Root launcher script
run_human_typer.bat       # Windows 1-click batch launcher
```
