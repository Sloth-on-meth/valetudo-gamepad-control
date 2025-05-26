# 🕹️ Valetudo PS4 Controller Interface
<p>
  <img src="https://img.shields.io/github/last-commit/sloth-on-meth/valetudo-gamepad-control?color=yellow" alt="Last Commit">
  <img src="https://img.shields.io/github/stars/sloth-on-meth/valetudo-gamepad-control?style=social" alt="Stars">
  <img src="https://img.shields.io/github/issues/sloth-on-meth/valetudo-gamepad-control" alt="Issues">
</p>



This Python script lets you control a [Valetudo](https://github.com/Hypfer/Valetudo)-compatible robot vacuum using a PS4 controller. The script sends HTTP API commands based on joystick input.

---

## ✨ Features

* 🎮 Move/rotate the robot using the joystick
* ❄️ Toggle fan speed with the **X** button
* 🚀 Toggle speed boost with the **Circle** button
* 🏠 Return the robot to the dock with the **Triangle** button
* 🎯 Smooth directional control with automatic speed scaling
* 🛡️ Built-in clamping and retry handling to prevent API errors

---

## 🎮 Controls

* **X (0)**: Toggle fan speed between max and off
* **Circle (1)**: Toggle speed boost (0.6 ⇄ 1.0)
* **Triangle (3)**: Stop remote control and send robot home
* **Left joystick**: Controls direction and speed
* **Square (2)**: Plays the test sound

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
