# Valetudo PS4 Controller Interface

This Python script allows you to control a Valetudo-compatible robot vacuum using a PS4 joystick via `pygame`, using HTTP API calls.

---

## Features

* **Manual joystick control** (forward, reverse, arc, spin)
* **Speed boost toggle** via Circle (O) button
* **Fan speed toggle** via X button (max/off)
* **Dock command** via Triangle button
* **Button press logging**
* **Velocity clamping** to prevent API errors

---

## Controls (PS4 Controller)

| Button       | Action                        |
| ------------ | ----------------------------- |
| X (0)        | Toggle fan speed (max/off)    |
| Circle (1)   | Toggle boost mode (0.6 / 1.0) |
| Triangle (3) | Return to dock (disables RC)  |
| Joystick     | Move/rotate robot             |

---

## Requirements

* Python 3.8+
* `pygame`
* `requests`

Install dependencies:

```bash
pip install pygame requests
```

---

## Usage

```bash
python3 controller.py
```

Make sure the PS4 controller is connected **before running the script**.

---

## Robot API Configuration

Make sure your robot is reachable at:

```
http://192.168.178.43
```

You can change this in the script by editing the `VALE_URL` variable.

---

## Endpoints Used

| Capability        | Endpoint                                                                        |
| ----------------- | ------------------------------------------------------------------------------- |
| Movement          | `/api/v2/robot/capabilities/HighResolutionManualControlCapability`              |
| Fan preset toggle | `/api/v2/robot/capabilities/FanSpeedControlCapability/preset`                   |
| Docking           | `/api/v2/robot/capabilities/BasicControlCapability` (with `{"action": "home"}`) |

---

## Notes

* All movement commands are rate-limited to avoid spamming the robot.
* Movement direction and speed are proportional to joystick tilt.
* `BOOST_SPEED` and `NORMAL_SPEED` are capped at 1.0.
* Docking disables manual mode before issuing the "home" command.

---

## License

MIT or WTFPL. You choose.

---

## Troubleshooting

* **Joystick not detected**: Ensure it's paired and connected before launching.
* **HTTP 400 errors**: Likely due to exceeding `velocity > 1.0`. Script clamps this now.
* **Fan errors**: Ensure your Valetudo firmware supports `FanSpeedControlCapability`.
* **Dock command fails**: Make sure to disable remote control before sending "home".
