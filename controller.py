import sys
import math
import asyncio
import pygame
import aiohttp

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
SEND_INTERVAL_MS = 100  # ms
COOLDOWN_MS = 300  # ms

# Globals
last_sent = {"angle": None, "velocity": None}
last_send_time = 0
cooldowns = {k: 0 for k in BUTTONS}
fan_state = "off"
boost_enabled = False


def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))


async def put(session, endpoint, payload, label="Request"):
    url = VALE_URL + endpoint
    try:
        async with session.put(url, json=payload, timeout=2) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"[!] {label} HTTP {resp.status}: {text}")
    except Exception as e:
        print(f"[!] {label} failed: {e}")


async def send_command(session, action, velocity=0.0, angle=0.0):
    global last_sent, last_send_time
    now = pygame.time.get_ticks()

    if action == "move":
        angle = round(angle, 1)
        velocity = round(clamp(velocity, -1.0, 1.0), 3)
        angle_changed = last_sent["angle"] is None or abs(angle - last_sent["angle"]) > ANGLE_EPSILON
        velocity_changed = last_sent["velocity"] is None or abs(velocity - last_sent["velocity"]) > VELOCITY_EPSILON
        if angle_changed or velocity_changed or (now - last_send_time) > SEND_INTERVAL_MS:
            await put(session, ENDPOINTS["control"], {"action": "move", "vector": {"velocity": velocity, "angle": angle}}, "Move")
            last_sent.update({"angle": angle, "velocity": velocity})
            last_send_time = now
    else:
        await put(session, ENDPOINTS["control"], {"action": action}, f"Control ({action})")


async def play_sound(session):
    await put(session, ENDPOINTS["sound"], {"action": "play_test_sound"}, "Sound")


async def toggle_fan(session):
    global fan_state
    fan_state = "max" if fan_state == "off" else "off"
    await put(session, ENDPOINTS["fan"], {"name": fan_state}, "Fan")
    print(f"[i] Fan set to {fan_state}")


async def send_dock_and_exit(session):
    print("[i] Disabling remote control...")
    await put(session, ENDPOINTS["control"], {"action": "disable"}, "Disable")
    await asyncio.sleep(2)
    print("[i] Sending dock command...")
    await put(session, ENDPOINTS["dock"], {"action": "home"}, "Dock")
    pygame.quit()
    sys.exit(0)


def cooldown_ready(key):
    now = pygame.time.get_ticks()
    if now - cooldowns[key] > COOLDOWN_MS:
        cooldowns[key] = now
        return True
    return False


async def handle_movement(session, x_axis, y_axis, boost):
    abs_x, abs_y = abs(x_axis), abs(y_axis)
    max_speed = BOOST_SPEED if boost else NORMAL_SPEED

    if abs_x < DEADZONE and abs_y < DEADZONE:
        await send_command(session, "move", 0.0, 0.0)
    elif abs_y > DEADZONE and abs_x < (DEADZONE * 1.5):
        # Straight forward or backward
        velocity = ((abs_y - DEADZONE) / (1 - DEADZONE)) * max_speed
        velocity = velocity if y_axis > 0 else -velocity
        await send_command(session, "move", clamp(velocity, -1.0, 1.0), 0.0)
    elif abs_x > DEADZONE and abs_y < (DEADZONE * 1.5):
        # Rotation only
        angle = 90 if x_axis > 0 else -90
        await send_command(session, "move", 0.0, angle)
    else:
        # Diagonal movement
        # Flip x-axis when going backwards to fix mirrored controls
        corrected_x = -x_axis if y_axis < 0 else x_axis
        angle_rad = math.atan2(corrected_x, y_axis)
        angle_deg = math.degrees(angle_rad)
        magnitude = math.sqrt(x_axis ** 2 + y_axis ** 2)
        velocity = ((max(0.0, magnitude - DEADZONE)) / (1 - DEADZONE)) * max_speed
        velocity = velocity if y_axis > 0 else -velocity
        await send_command(session, "move", clamp(velocity, -1.0, 1.0), angle_deg)



async def main():
    global boost_enabled

    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick detected.")
        sys.exit(1)

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Using joystick: {js.get_name()}")

    async with aiohttp.ClientSession() as session:
        await send_command(session, "enable")
        clock = pygame.time.Clock()

        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        raise KeyboardInterrupt

                x_axis = js.get_axis(0)
                y_axis = -js.get_axis(1)
                now = pygame.time.get_ticks()

                if js.get_button(BUTTONS["x"]) and cooldown_ready("x"):
                    await toggle_fan(session)

                if js.get_button(BUTTONS["circle"]) and cooldown_ready("circle"):
                    boost_enabled = not boost_enabled
                    print(f"[i] Boost {'enabled' if boost_enabled else 'disabled'}")

                if js.get_button(BUTTONS["square"]) and cooldown_ready("square"):
                    await play_sound(session)

                if js.get_button(BUTTONS["triangle"]) and cooldown_ready("triangle"):
                    await send_dock_and_exit(session)

                await handle_movement(session, x_axis, y_axis, boost_enabled)
                clock.tick(60)

        except KeyboardInterrupt:
            print("Exiting...")
        finally:
            try:
                await send_command(session, "move", 0.0, 0.0)
                await asyncio.sleep(0.1)
                await send_command(session, "disable")
            except Exception as e:
                print(f"[!] Cleanup error: {e}")
            finally:
                pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())
