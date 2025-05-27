import asyncio
import aiohttp
import curses
import pygame
import math
import sys
import subprocess

VALE_URL = "http://192.168.178.43"
STATE_URL = f"{VALE_URL}/api/v2/robot/state/"
CONTROL_URL = f"{VALE_URL}/api/v2/robot/capabilities/HighResolutionManualControlCapability"
SOUND_URL = f"{VALE_URL}/api/v2/robot/capabilities/SpeakerTestCapability"
DOCK_URL = f"{VALE_URL}/api/v2/robot/capabilities/BasicControlCapability"
FAN_URL = f"{VALE_URL}/api/v2/robot/capabilities/FanSpeedControlCapability/preset"

SPEED_LEVELS = [0.1, 0.6, 1.0]
DEADZONE = 0.15
ANGLE_EPSILON = 3
VELOCITY_EPSILON = 0.02
SEND_INTERVAL_MS = 100

speed_index = 1
fan_state = "off"
robot_battery = "?"
controller_battery = "?"
x_axis = 0.0
y_axis = 0.0
last_sent = {"angle": None, "velocity": None}
last_send_time = 0

def clamp(val, min_val, max_val):
    return max(min_val, min(val, max_val))

async def get_robot_battery(session):
    try:
        async with session.get(STATE_URL, timeout=2) as resp:
            data = await resp.json()
            for attr in data.get("attributes", []):
                if attr.get("__class") == "BatteryStateAttribute":
                    return attr.get("level", "?")
    except:
        return "?"

async def send_command(session, velocity, angle):
    global last_sent, last_send_time
    now = pygame.time.get_ticks()
    angle = round(angle, 1)
    velocity = round(clamp(velocity, -1.0, 1.0), 3)
    angle_changed = last_sent["angle"] is None or abs(angle - last_sent["angle"]) > ANGLE_EPSILON
    velocity_changed = last_sent["velocity"] is None or abs(velocity - last_sent["velocity"]) > VELOCITY_EPSILON
    if angle_changed or velocity_changed or (now - last_send_time) > SEND_INTERVAL_MS:
        payload = {
            "action": "move",
            "vector": {
                "velocity": velocity,
                "angle": angle
            }
        }
        try:
            async with session.put(CONTROL_URL, json=payload, timeout=2):
                last_sent = {"angle": angle, "velocity": velocity}
                last_send_time = now
        except Exception as e:
            print(f"[!] Failed to send command: {e}")

async def play_sound(session):
    try:
        await session.put(SOUND_URL, json={"action": "play_test_sound"})
    except Exception as e:
        print(f"[!] Failed to play sound: {e}")

async def send_dock(session):
    try:
        await session.put(DOCK_URL, json={"action": "home"})
    except Exception as e:
        print(f"[!] Failed to dock: {e}")
FAN_STATES = ["off", "max"]
fan_state_index = 0

async def toggle_fan(session):
    global fan_state, fan_state_index
    fan_state_index = (fan_state_index + 1) % len(FAN_STATES)
    fan_state = FAN_STATES[fan_state_index]
    try:
        async with session.put(FAN_URL, json={"name": fan_state}, timeout=2) as resp:
            if resp.status != 200:
                text = await resp.text()
                print(f"[!] Fan HTTP {resp.status}: {text}")
            else:
                print(f"[i] Fan set to {fan_state}")
    except Exception as e:
        print(f"[!] Failed to set fan: {e}")



async def poll_robot_battery(session):
    global robot_battery
    while True:
        robot_battery = await get_robot_battery(session)
        await asyncio.sleep(5)

async def read_joystick_input(session):
    global x_axis, y_axis, speed_index
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("No joystick connected.")
        return

    js = pygame.joystick.Joystick(0)
    js.init()

    while True:
        pygame.event.pump()
        x_axis = js.get_axis(0)
        y_axis = -js.get_axis(1)

        if js.get_button(0):  # X
            await toggle_fan(session)
            await asyncio.sleep(0.3)

        if js.get_button(1):  # CIRCLE
            speed_index = (speed_index + 1) % len(SPEED_LEVELS)
            await asyncio.sleep(0.3)

        if js.get_button(2):  # SQUARE
            await play_sound(session)
            await asyncio.sleep(0.3)

        if js.get_button(3):  # TRIANGLE
            await send_dock(session)
            await asyncio.sleep(0.3)

        abs_x, abs_y = abs(x_axis), abs(y_axis)
        max_speed = SPEED_LEVELS[speed_index]

        if abs_x < DEADZONE and abs_y < DEADZONE:
            await send_command(session, 0.0, 0.0)
        elif abs_y > DEADZONE and abs_x < (DEADZONE * 1.5):
            velocity = ((abs_y - DEADZONE) / (1 - DEADZONE)) * max_speed
            velocity = velocity if y_axis > 0 else -velocity
            await send_command(session, clamp(velocity, -1.0, 1.0), 0.0)
        elif abs_x > DEADZONE and abs_y < (DEADZONE * 1.5):
            angle = 90 if x_axis > 0 else -90
            await send_command(session, 0.0, angle)
        else:
            corrected_x = -x_axis if y_axis < 0 else x_axis
            angle_rad = math.atan2(corrected_x, y_axis)
            angle_deg = math.degrees(angle_rad)
            magnitude = math.sqrt(x_axis ** 2 + y_axis ** 2)
            velocity = ((max(0.0, magnitude - DEADZONE)) / (1 - DEADZONE)) * max_speed
            velocity = velocity if y_axis > 0 else -velocity
            await send_command(session, clamp(velocity, -1.0, 1.0), angle_deg)

        await asyncio.sleep(0.01)

async def draw_tui_labels(stdscr):
    global robot_battery, speed_index, fan_state
    while True:
        stdscr.addstr(0, 0, "Valetudo TUI")
        stdscr.addstr(2, 0, f"Robot battery:     {robot_battery}%   ")
        stdscr.addstr(3, 0, f"Speed level:       {SPEED_LEVELS[speed_index]}    ")
        stdscr.addstr(4, 0, f"Fan mode:          {fan_state}       ")
        stdscr.addstr(6, 0, "X: Toggle fan mode")
        stdscr.addstr(7, 0, "Circle: Cycle speed")
        stdscr.addstr(8, 0, "Square: Play sound")
        stdscr.addstr(9, 0, "Triangle: Dock robot")
        stdscr.refresh()
        await asyncio.sleep(1.0)

async def draw_tui_joystick(stdscr):
    global x_axis, y_axis
    while True:
        stdscr.addstr(11, 0, "Joystick X: [{:<20}] {:.2f} ".format("=" * int((x_axis + 1) * 10), x_axis))
        stdscr.addstr(12, 0, "Joystick Y: [{:<20}] {:.2f} ".format("=" * int((y_axis + 1) * 10), y_axis))
        stdscr.refresh()
        await asyncio.sleep(0.1)

async def main(stdscr):
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(
            draw_tui_labels(stdscr),
            draw_tui_joystick(stdscr),
            poll_robot_battery(session),
            read_joystick_input(session)
        )

if __name__ == "__main__":
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr)))
