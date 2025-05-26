# Valetudo PS4 Controller Interface


#As i am banned from the Valetudo telegram, i am unable to chat with you guys there. makes me sad :(

This script allows you to control a Valetudo-powered vacuum (e.g. Roborock S5) using a PS4 controller via `pygame` and Valetudo's `HighResolutionManualControlCapability`.

---

## Requirements

* Python 3.x
* `pygame`
* `requests`
* Valetudo with `HighResolutionManualControlCapability` enabled

---

## Installation

```bash
pip install pygame requests
```

---

## Configuration

Edit these values in the script if needed:

```python
VALE_URL = "http://192.168.178.43"  # Your vacuum's IP
MAX_SPEED = 0.4                      # Max velocity in m/s
DEADZONE = 0.15                      # Joystick deadzone
```

---

## Controls

* Left stick: Move the robot (directional angle + velocity)
* Ctrl+C: Exit and disable remote control mode cleanly

---

## How it works

* Sends `{ "action": "enable" }` to start manual control
* Converts left stick input into a polar vector (`velocity`, `angle`)
* Sends only meaningful changes (smoothed + throttled)
* On exit:

  * Sends stop (`velocity: 0.0`)
  * Sends `{ "action": "disable" }` to exit manual mode

---

## Example Output

```text
Using joystick: PS4 Controller
Sending stop and ending remote control mode...
Remote control mode exited.
```

---

## Troubleshooting

* If the robot doesn't move:

  * Make sure `HighResolutionManualControlCapability` is listed at `/api/v2/robot/capabilities`
  * Ensure manual mode is enabled with `{ "action": "enable" }`
* Some Roborock firmware requires low velocities (< 0.4 m/s)

---


