[![GitHub stars](https://img.shields.io/github/stars/Sloth-on-meth/valetudo-gamepad-control?style=social)](https://github.com/Sloth-on-meth/valetudo-gamepad-control/stargazers)
[![Commits](https://img.shields.io/github/commit-activity/m/Sloth-on-meth/valetudo-gamepad-control)](https://github.com/Sloth-on-meth/valetudo-gamepad-control/commits/master)

# Valetudo Gamepad Control

Control your Valetudo-powered robot vacuum with a game controller — now with real-time joystick input, async network commands, and a terminal-based UI (TUI) for visual feedback.

---

## 🚀 Features

* 🎮 Smooth joystick control via PlayStation/Xbox controller
* ⚡ Toggle speed level (Circle)
* 🄀 Visualize joystick axes in real-time
* 🔊 Play test sound (Square)
* 🏠 Return to dock and quit (Triangle)
* 🧠 Async `aiohttp` backend for snappy control
* 🔢 Terminal UI (TUI) built with `curses`
* ❌ Cooldown-based button debounce (no double actions)

---

## 🧪 Requirements

* Python 3.8+
* A robot vacuum running Valetudo > 2025.05.0 (with `HighResolutionManualControlCapability`)
* A joystick/gamepad supported by [pygame](https://www.pygame.org/)
* `aiohttp`, `pygame`, `curses` (built-in on Linux/macOS)

```bash
pip install -r requirements.txt
# or individually
pip install aiohttp pygame
```

---

## 🎮 Controls

| Button     | Action              |
| ---------- | ------------------- |
| Left Stick | Move the robot      |
| Circle     | Cycle speed level   |
| Square     | Play test sound     |
| Triangle   | Dock robot and exit |

---

## 🛠️ Usage

1. Connect your gamepad
2. Edit `VALE_URL` in `controller.py` to match your robot's IP
3. Run:

```bash
python controller.py
```

4. Control the robot with the left stick. Use buttons as described above.

---

## 🌟 TUI Display

* Real-time joystick position bars
* Battery level of robot (polled every 5s)
* Current speed level
* Button guide
