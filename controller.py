import pygame
import requests
import math
import sys
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

VALE_URL = "http://192.168.178.43"
CONTROL_ENDPOINT = "/api/v2/robot/capabilities/HighResolutionManualControlCapability"
FAN_ENDPOINT = "/api/v2/robot/capabilities/FanSpeedControlCapability/preset"
DOCK_ENDPOINT = "/api/v2/robot/capabilities/BasicControlCapability"

DEADZONE = 0.15
NORMAL_SPEED = 0.6
BOOST_SPEED = 1.0
ANGLE_EPSILON = 3
VELOCITY_EPSILON = 0.02
SEND_INTERVAL = 0.1

X_BUTTON_INDEX = 0       # X = toggle fan
CIRCLE_BUTTON_INDEX = 1  # Circle = toggle boost
TRIANGLE_BUTTON_INDEX = 3  # Triangle = return to dock

last_sent = {"angle": None, "velocity": None}
last_send_time = 0.0
fan_state = "off"
boost_enabled = False
boost_toggle_state = False
dock_toggle_state = False

session = requests.Session()
retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))


def send_command(action, velocity=0.0, angle=0.0):
    global last_sent, last_send_time
    now = time.time()

    if action == "move":
        angle = round(angle, 1)
        velocity = round(min(1.0, velocity), 3)

        angle_changed = last_sent["angle"] is None or abs(angle - last_sent["angle"]) > ANGLE_EPSILON
        velocity_changed = last_sent["velocity"] is None or abs(velocity - last_sent["velocity"]) > VELOCITY_EPSILON
        time_elapsed = (now - last_send_time) > SEND_INTERVAL

        if angle_changed or velocity_changed or time_elapsed:
            payload = {
                "action": "move",
                "vector": {
                    "velocity": float(velocity),
                    "angle": float(angle)
                }
            }
            try:
                r = session.put(VALE_URL + CONTROL_ENDPOINT, json=payload, timeout=2)
                if r.status_code != 200:
                    print(f"[!] HTTP {r.status_code}: {r.text}")
            except Exception as e:
                print(f"[!] Request failed: {e}")

            last_sent["angle"] = angle
            last_sent["velocity"] = velocity
            last_send_time = now

    elif action in ("enable", "disable"):
        try:
            r = session.put(VALE_URL + CONTROL_ENDPOINT, json={"action": action}, timeout=2)
            if r.status_code != 200:
                print(f"[!] HTTP {r.status_code}: {r.text}")
        except Exception as e:
            print(f"[!] Request failed: {e}")


def toggle_fan():
    global fan_state
    fan_state = "max" if fan_state == "off" else "off"
    try:
        r = session.put(VALE_URL + FAN_ENDPOINT, json={"name": fan_state}, timeout=2)
        if r.status_code != 200:
            print(f"[!] Fan HTTP {r.status_code}: {r.text}")
        else:
            print(f"[i] Fan set to {fan_state}")
    except Exception as e:
        print(f"[!] Fan request failed: {e}")


def send_dock():
    try:
        # Disable manual control first
        r1 = session.put(VALE_URL + CONTROL_ENDPOINT, json={"action": "disable"}, timeout=2)
        if r1.status_code != 200:
            print(f"[!] Failed to disable manual control: {r1.status_code} {r1.text}")
            return

        # Send dock command
        r2 = session.put(VALE_URL + "/api/v2/robot/capabilities/BasicControlCapability",
                         json={"action": "home"}, timeout=2)
        if r2.status_code != 200:
            print(f"[!] Dock HTTP {r2.status_code}: {r2.text}")
        else:
            print("[i] Return to dock command sent")

    except Exception as e:
        print(f"[!] Dock request failed: {e}")



def main():
    global boost_enabled, boost_toggle_state, dock_toggle_state

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick detected.")
        sys.exit(1)

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Using joystick: {js.get_name()}")

    send_command("enable")

    try:
        clock = pygame.time.Clock()
        fan_button_state = False

        while True:
            pygame.event.pump()

            # Print button presses
            for i in range(js.get_numbuttons()):
                if js.get_button(i):
                    print(f"Button {i} pressed")

            x_axis = js.get_axis(0)
            y_axis = -js.get_axis(1)

            x_button = js.get_button(X_BUTTON_INDEX)
            circle_button = js.get_button(CIRCLE_BUTTON_INDEX)
            triangle_button = js.get_button(TRIANGLE_BUTTON_INDEX)

            # Toggle fan (X)
            if x_button and not fan_button_state:
                toggle_fan()
                fan_button_state = True
            elif not x_button:
                fan_button_state = False

            # Toggle boost (Circle)
            if circle_button and not boost_toggle_state:
                boost_enabled = not boost_enabled
                print(f"[i] Boost {'enabled' if boost_enabled else 'disabled'}")
                boost_toggle_state = True
            elif not circle_button:
                boost_toggle_state = False

            # Return to dock (Triangle)
            if triangle_button and not dock_toggle_state:
                send_dock()
                dock_toggle_state = True
            elif not triangle_button:
                dock_toggle_state = False

            max_speed = BOOST_SPEED if boost_enabled else NORMAL_SPEED
            abs_x = abs(x_axis)
            abs_y = abs(y_axis)

            if abs_x < DEADZONE and abs_y < DEADZONE:
                send_command("move", velocity=0.0, angle=0.0)

            elif abs_y > DEADZONE and abs_x < (DEADZONE * 1.5):
                angle_deg = 0 if y_axis > 0 else 180
                norm_mag = (abs(y_axis) - DEADZONE) / (1 - DEADZONE)
                velocity = norm_mag * max_speed
                if y_axis < 0:
                    velocity = -velocity
                send_command("move", velocity=velocity, angle=angle_deg)

            elif abs_x > DEADZONE and abs_y < (DEADZONE * 1.5):
                angle_deg = 90 if x_axis > 0 else -90
                send_command("move", velocity=0.0, angle=angle_deg)

            else:
                angle_rad = math.atan2(x_axis, y_axis)
                angle_deg = math.degrees(angle_rad)
                magnitude = math.sqrt(x_axis ** 2 + y_axis ** 2)
                norm_mag = max(0.0, (magnitude - DEADZONE) / (1 - DEADZONE))
                velocity = norm_mag * max_speed
                if y_axis < 0:
                    velocity = -velocity
                send_command("move", velocity=velocity, angle=angle_deg)

            clock.tick(60)

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        try:
            print("Sending stop and ending remote control mode...")
            send_command("move", velocity=0.0, angle=0.0)
            time.sleep(0.1)
            send_command("disable")
            print("Remote control mode exited.")
        except Exception as e:
            print(f"[!] Failed to exit cleanly: {e}")
        finally:
            pygame.quit()


if __name__ == "__main__":
    main()
