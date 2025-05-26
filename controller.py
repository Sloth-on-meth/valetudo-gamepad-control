import pygame
import requests
import math
import sys

VALE_URL = "http://192.168.178.43"
ENDPOINT = "/api/v2/robot/capabilities/HighResolutionManualControlCapability"
DEADZONE = 0.15
MAX_SPEED = 0.4
ANGLE_EPSILON = 3      # Degrees
VELOCITY_EPSILON = 0.02
SEND_INTERVAL = 0.1    # Seconds

last_sent = {"angle": None, "velocity": None}
last_send_time = 0.0


def send_command(action, velocity=0.0, angle=0.0):
    global last_sent, last_send_time
    now = time.time()

    if action == "move":
        angle = round(angle, 1)
        velocity = round(velocity, 3)

        # Only send if different or time threshold passed
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
                r = requests.put(VALE_URL + ENDPOINT, json=payload, timeout=1)
                if r.status_code != 200:
                    print(f"[!] HTTP {r.status_code}: {r.text}")
            except Exception as e:
                print(f"[!] Request failed: {e}")

            last_sent["angle"] = angle
            last_sent["velocity"] = velocity
            last_send_time = now

    elif action in ("enable", "disable"):
        try:
            r = requests.put(VALE_URL + ENDPOINT, json={"action": action}, timeout=1)
            if r.status_code != 200:
                print(f"[!] HTTP {r.status_code}: {r.text}")
        except Exception as e:
            print(f"[!] Request failed: {e}")


def main():
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
        while True:
            pygame.event.pump()

            x = js.get_axis(0)
            y = -js.get_axis(1)

            if abs(x) < DEADZONE and abs(y) < DEADZONE:
                send_command("move", velocity=0.0, angle=0.0)
            else:
                angle_rad = math.atan2(x, y)
                angle_deg = math.degrees(angle_rad)
                magnitude = math.sqrt(x**2 + y**2)
                velocity = min(MAX_SPEED, magnitude * MAX_SPEED)

                send_command("move", velocity=velocity, angle=angle_deg)

            clock.tick(60)

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        send_command("move", velocity=0.0, angle=0.0)
        send_command("disable")
        pygame.quit()


if __name__ == "__main__":
    import time
    main()
#test