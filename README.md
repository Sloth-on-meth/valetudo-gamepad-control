# Valetudo Gamepad Control

Control your Valetudo-powered robot vacuum with a game controller — now with real-time joystick input, async network commands, and optional boost/fan/sound controls.

---

## 🚀 Features

* 🎮 Smooth joystick control via PlayStation/Xbox controller
* ⚡ Toggle boost mode (Circle)
* 🂀 Toggle fan power (X)
* 🔊 Play test sound (Square)
* 🏠 Return to dock and quit (Triangle)
* 🧠 Async `aiohttp` backend for snappy control
* 🢼 Graceful cleanup and velocity/angle optimizations
* 🚫 Cooldown-based button debounce (no double actions)

---

## 🧪 Requirements

* Python 3.8+
* Valetudo (with HighResolutionManualControlCapability enabled)
* A joystick/gamepad supported by [pygame](https://www.pygame.org/)
* `aiohttp`, `pygame`:

```bash
pip install -r requirements.txt
# or individually
pip3 install aiohttp pygame
```

---

## 🎮 Controls

| Button     | Action               |
| ---------- | -------------------- |
| Left Stick | Move the robot       |
| Circle     | Toggle boost mode    |
| X          | Toggle fan (off/max) |
| Square     | Play test sound      |
| Triangle   | Dock robot and exit  |

---

## 🛠️ Usage

1. Plug in your gamepad
2. Edit `VALE_URL` in `controller.py` if needed
3. Run:

```bash
python controller.py
```

4. Move the robot with the stick. Use buttons as described above.



## ❓ Contributing

PRs welcome! Fork, branch, make it better, send it back.
