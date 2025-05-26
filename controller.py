import pygame
import requests
import math
import sys

# Config
VALE_URL = "http://192.168.178.43"
ENDPOINT = "/api/v2/robot/capabilities/HighResolutionManualControlCapability"
DEADZONE = 0.1
MAX_SPEED = 0.4  # max velocity in m/s
FPS = 20


def send_command(action, velocity=0.0, angle=0.0):
    url = VALE_URL + ENDPOINT
    headers = {"Content-Type": "application/json"}

    if action == "move":
        payload = {
            "action": "move",
            "vector": {
                "velocity": float(velocity),
                "angle": float(angle)
            }
        }
    else:
        payload = {"action": action}

    try:
        r = requests.put(url, json=payload, headers=headers, timeout=1)
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

            x = js.get_axis(0)  # left/right
            y = -js.get_axis(1)  # up/down

            if abs(x) < DEADZONE and abs(y) < DEADZONE:
                send_command("move", velocity=0.0, angle=0.0)
            else:
                angle_rad = math.atan2(x, y)  # note: x and y are flipped to match expected orientation
                angle_deg = math.degrees(angle_rad)
                magnitude = math.sqrt(x**2 + y**2)
                velocity = min(MAX_SPEED, magnitude * MAX_SPEED)
                send_command("move", velocity=velocity, angle=angle_deg)

            clock.tick(FPS)

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        send_command("move", velocity=0.0, angle=0.0)
        send_command("disable")
        pygame.quit()


if __name__ == "__main__":
    main()
