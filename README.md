# 🕹️ Valetudo PS4 Controller Interface

<p align="center">
  <img src="https://img.shields.io/badge/python-3.8+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT%20%7C%20WTFPL-brightgreen" alt="License">
  <img src="https://img.shields.io/badge/valetudo-compatible-orange" alt="Valetudo Compatible">
  <img src="https://img.shields.io/badge/controller-PS4-purple" alt="PS4 Controller">
  <img src="https://img.shields.io/github/last-commit/yourusername/valetudo-ps4-controller?color=yellow" alt="Last Commit">
  <img src="https://img.shields.io/github/stars/yourusername/valetudo-ps4-controller?style=social" alt="Stars">
  <img src="https://img.shields.io/github/issues/yourusername/valetudo-ps4-controller" alt="Issues">
</p>

![License](https://img.shields.io/badge/license-MIT%20%7C%20WTFPL-brightgreen)
![Valetudo](https://img.shields.io/badge/valetudo-compatible-orange)
![Controller](https://img.shields.io/badge/controller-PS4-purple)

This Python script lets you control a Valetudo-compatible robot vacuum using a PS4 controller. The script sends HTTP API commands based on joystick input.

---

## ✨ Features

* 🎮 Move/rotate the robot using the joystick
* ❄️ Toggle fan speed with the **X** button
* 🚀 Toggle speed boost with the **Circle** button
* 🏠 Return the robot to the dock with the **Triangle** button
* 🎯 Smooth directional control with automatic speed scaling
* 🛡️ Built-in clamping and retry handling to prevent API abuse/errors

---

## 🎮 Controls

* **X (0)**: Toggle fan speed between max and off
* **Circle (1)**: Toggle speed boost (0.6 ⇄ 1.0)
* **Triangle (3)**: Stop remote control and send robot home
* **Left joystick**: Controls direction and speed

---

## ⚙️ Setup Requirements

* Python 3.8 or newer
* Dependencies:

```bash
pip install pygame requests
```

---

## 🚀 Usage

1. Make sure your PS4 controller is connected.
2. Open `controller.py` in your editor.
3. Edit the following line to point to your Valetudo robot:

```python
VALE_URL = "http://192.168.178.43"
```

4. Run the script:

```bash
python3 controller.py
```

---

## 📡 API Endpoints Used

* `HighResolutionManualControlCapability` for directional control
* `FanSpeedControlCapability/preset` to toggle fan speed
* `BasicControlCapability` with `{ "action": "home" }` to send robot to the dock

---

## 📝 Notes

* Remote control is automatically disabled before sending the robot home.
* Speed is dynamically scaled based on joystick tilt.
* Movement commands are rate-limited to prevent flooding.
* Velocity is clamped to avoid exceeding robot limits.
