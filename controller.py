import sys
import time
import math
import pygame
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
VALE_URL = "http://192.168.178.43"
ENDPOINTS = {
    "control": "/api/v2/robot/capabilities/HighResolutionManualControlCapability",
    "fan": "/api/v2/robot/capabilities/FanSpeedControlCapability/preset",
    "dock": "/api/v2/robot/capabilities/BasicControlCapability",
    "sound": "/api/v2/robot/capabilities/SpeakerTestCapability"
}

BUTTONS = {
    "x": 0,
    "circle": 1,
    "square": 2,
    "triangle": 3
}

DEADZONE = 0.15
NORMAL_SPEED = 0.6
BOOST_SPEED = 1.0
ANGLE_EPSILON = 3
VELOCITY_EPSILON = 0.02
SEND_INTERVAL = 0.1

# Globals
last_sent = {"angle": None, "velocity": None}
last_send_time = 0
fan_state = "off"
boost_enabled = False
toggle_states = {"boost": False, "dock": False, "fan": False}

# Setup HTTP session with retries
session = requests.Session()
retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))


# Utility functions
def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))


def put(endpoint, payload, label="Request"):
    try:
        r = session.put(VALE_URL + endpoint, json=payload, timeout=2)
        if r.status_code != 200:
            print(f"[!] {label} HTTP {r.status_code}: {r.text}")
        return r
    except Exception as e:
        print(f"[!] {label} failed: {e}")


# Action functions
def send_command(action, velocity=0.0, angle=0.0):
    global last_sent, last_send_time
    now = time.time()

    if action == "move":
        angle = round(angle, 1)
        velocity = round(clamp(velocity, -1.0, 1.0), 3)

        angle_changed = last_sent["angle"] is None or abs(angle - last_sent["angle"]) > ANGLE_EPSILON
        velocity_changed = last_sent["velocity"] is None or abs(velocity - last_sent["velocity"]) > VELOCITY_EPSILON
        if angle_changed or velocity_changed or (now - last_send_time) > SEND_INTERVAL:
            put(ENDPOINTS["control"], {"action": "move", "vector": {"velocity": velocity, "angle": angle}}, "Move")
            last_sent.update({"angle": angle, "velocity": velocity})
            last_send_time = now
    else:
        put(ENDPOINTS["control"], {"action": action}, f"Control ({action})")


def play_sound():
    put(ENDPOINTS["sound"], {"action": "play_test_sound"}, "Sound")


def toggle_fan():
    global fan_state
    fan_state = "max" if fan_state == "off" else "off"
    put(ENDPOINTS["fan"], {"name": fan_state}, "Fan")
    print(f"[i] Fan set to {fan_state}")


def send_dock_and_exit():
    print("[i] Disabling remote control...")
    put(ENDPOINTS["control"], {"action": "disable"}, "Disable")
    time.sleep(2)
    print("[i] Sending dock command...")
    put(ENDPOINTS["dock"], {"action": "home"}, "Dock")
    pygame.quit()
    sys.exit(0)


# Main loop
def main():
    global boost_enabled

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick detected.")
        sys.exit(1)

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Using joystick: {js.get_name()}")

    send_command("enable")
    clock = pygame.time.Clock()

    try:
        while True:
            pygame.event.pump()

            x_axis = js.get_axis(0)
            y_axis = -js.get_axis(1)

            # Handle buttons
            if js.get_button(BUTTONS["x"]) and not toggle_states["fan"]:
                toggle_fan()
                toggle_states["fan"] = True
            elif not js.get_button(BUTTONS["x"]):
                toggle_states["fan"] = False

            if js.get_button(BUTTONS["circle"]) and not toggle_states["boost"]:
                boost_enabled = not boost_enabled
                print(f"[i] Boost {'enabled' if boost_enabled else 'disabled'}")
                toggle_states["boost"] = True
            elif not js.get_button(BUTTONS["circle"]):
                toggle_states["boost"] = False

            if js.get_button(BUTTONS["square"]):
                play_sound()

            if js.get_button(BUTTONS["triangle"]) and not toggle_states["dock"]:
                toggle_states["dock"] = True
                send_dock_and_exit()
            elif not js.get_button(BUTTONS["triangle"]):
                toggle_states["dock"] = False

            # Movement
            abs_x, abs_y = abs(x_axis), abs(y_axis)
            max_speed = BOOST_SPEED if boost_enabled else NORMAL_SPEED

            if abs_x < DEADZONE and abs_y < DEADZONE:
                send_command("move", 0.0, 0.0)
            elif abs_y > DEADZONE and abs_x < (DEADZONE * 1.5):
                angle = 0 if y_axis > 0 else 180
                velocity = ((abs_y - DEADZONE) / (1 - DEADZONE)) * max_speed
                send_command("move", clamp(velocity if y_axis > 0 else -velocity, -1.0, 1.0), angle)
            elif abs_x > DEADZONE and abs_y < (DEADZONE * 1.5):
                angle = 90 if x_axis > 0 else -90
                send_command("move", 0.0, angle)
            else:
                angle_rad = math.atan2(x_axis, y_axis)
                angle_deg = math.degrees(angle_rad)
                magnitude = math.sqrt(x_axis**2 + y_axis**2)
                velocity = ((max(0.0, magnitude - DEADZONE)) / (1 - DEADZONE)) * max_speed
                send_command("move", clamp(velocity if y_axis > 0 else -velocity, -1.0, 1.0), angle_deg)

            clock.tick(60)

    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        try:
            send_command("move", 0.0, 0.0)
            time.sleep(0.1)
            send_command("disable")
        except Exception as e:
            print(f"[!] Cleanup error: {e}")
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
