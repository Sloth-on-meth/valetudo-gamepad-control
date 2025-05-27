[![GitHub stars](https://img.shields.io/github/stars/Sloth-on-meth/valetudo-gamepad-control?style=social)](https://github.com/Sloth-on-meth/valetudo-gamepad-control/stargazers)
[![Commits](https://img.shields.io/github/commit-activity/m/Sloth-on-meth/valetudo-gamepad-control)](https://github.com/Sloth-on-meth/valetudo-gamepad-control/commits/master)

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
* a robot vacuum running Valetudo > 2025.05.0 (with HighResolutionManualControlCapability)
* A joystick/gamepad supported by [pygame](https://www.pygame.org/)
* `aiohttp`, `pygame`:

```bash
pip install -r requirements.txt
# or individually
pip install aiohttp pygame
```

---

## Known issues

 - it is currently not possible to go straight backwards using this script, have not been able to figure it out.
   i wanted to ask hypfer about this, but i am banned from the telegram chat and github for some odd reason.
 
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

1. connect your gamepad
2. Edit `VALE_URL` in `controller.py` if needed
3. Run:

```bash
python controller.py
```

4. Move the robot with the stick. Use buttons as described above.

---

##
