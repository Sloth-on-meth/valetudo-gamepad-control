import os
import asyncio
import aiohttp
import curses
import pygame
import math
import logging
from typing import Optional

# Configuration
VALETUDO_URL = os.getenv("VALETUDO_URL", "http://192.168.178.43")
STATE_URL = f"{VALETUDO_URL}/api/v2/robot/state/"
CONTROL_URL = f"{VALETUDO_URL}/api/v2/robot/capabilities/HighResolutionManualControlCapability"
SOUND_URL = f"{VALETUDO_URL}/api/v2/robot/capabilities/SpeakerTestCapability"
DOCK_URL = f"{VALETUDO_URL}/api/v2/robot/capabilities/BasicControlCapability"
FAN_URL = f"{VALETUDO_URL}/api/v2/robot/capabilities/FanSpeedControlCapability/preset"

SPEED_LEVELS = [0.1, 0.6, 1.0]
FAN_STATES = ["off", "max"]
DEADZONE = 0.15
ANGLE_EPSILON = 3
VELOCITY_EPSILON = 0.02
SEND_INTERVAL_MS = 100

logging.basicConfig(level=logging.INFO)

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(val, max_val))

class RobotAPI:
    """Handles all robot-related API calls."""

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.last_sent = {"angle": None, "velocity": None}
        self.last_send_time = 0

    async def get_battery(self) -> Optional[int]:
        try:
            async with self.session.get(STATE_URL, timeout=2) as resp:
                data = await resp.json()
                for attr in data.get("attributes", []):
                    if attr.get("__class") == "BatteryStateAttribute":
                        return attr.get("level", "?")
        except Exception as e:
            logging.warning(f"Failed to get battery level: {e}")
        return "?"

    async def send_command(self, velocity: float, angle: float):
        now = pygame.time.get_ticks()
        angle = round(angle, 1)
        velocity = round(clamp(velocity, -1.0, 1.0), 3)
        angle_changed = self.last_sent["angle"] is None or abs(angle - self.last_sent["angle"]) > ANGLE_EPSILON
        velocity_changed = self.last_sent["velocity"] is None or abs(velocity - self.last_sent["velocity"]) > VELOCITY_EPSILON
        if angle_changed or velocity_changed or (now - self.last_send_time) > SEND_INTERVAL_MS:
            payload = {
                "action": "move",
                "vector": {"velocity": velocity, "angle": angle}
            }
            try:
                async with self.session.put(CONTROL_URL, json=payload, timeout=2):
                    self.last_sent = {"angle": angle, "velocity": velocity}
                    self.last_send_time = now
            except Exception as e:
                logging.warning(f"Failed to send command: {e}")

    async def play_sound(self):
        try:
            await self.session.put(SOUND_URL, json={"action": "play_test_sound"})
        except Exception as e:
            logging.warning(f"Failed to play sound: {e}")

    async def dock(self):
        try:
            await self.session.put(DOCK_URL, json={"action": "home"})
        except Exception as e:
            logging.warning(f"Failed to dock: {e}")

    async def set_fan(self, fan_state: str):
        try:
            async with self.session.put(FAN_URL, json={"name": fan_state}, timeout=2) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logging.warning(f"Fan HTTP {resp.status}: {text}")
                else:
                    logging.info(f"Fan set to {fan_state}")
        except Exception as e:
            logging.warning(f"Failed to set fan: {e}")

class JoystickController:
    """Handles joystick input and state."""

    def __init__(self):
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            raise RuntimeError("No joystick connected.")
        self.js = pygame.joystick.Joystick(0)
        self.js.init()
        self.x_axis = 0.0
        self.y_axis = 0.0
        self.speed_index = 1
        self.fan_index = 0

    def poll(self):
        pygame.event.pump()
        self.x_axis = self.js.get_axis(0)
        self.y_axis = -self.js.get_axis(1)
        return self.x_axis, self.y_axis

    def button_pressed(self, idx: int) -> bool:
        return self.js.get_button(idx)

    def cycle_speed(self):
        self.speed_index = (self.speed_index + 1) % len(SPEED_LEVELS)
        return self.speed_index

    def cycle_fan(self):
        self.fan_index = (self.fan_index + 1) % len(FAN_STATES)
        return FAN_STATES[self.fan_index]

class ValetudoTUI:
    """Handles the curses-based TUI."""

    def __init__(self, stdscr):
        self.stdscr = stdscr

    def draw_labels(self, robot_battery, speed_index, fan_state):
        self.stdscr.addstr(0, 0, "Valetudo TUI")
        self.stdscr.addstr(2, 0, f"Robot battery:     {robot_battery}%   ")
        self.stdscr.addstr(3, 0, f"Speed level:       {SPEED_LEVELS[speed_index]}    ")
        self.stdscr.addstr(4, 0, f"Fan mode:          {fan_state}       ")
        self.stdscr.addstr(6, 0, "X: Toggle fan mode")
        self.stdscr.addstr(7, 0, "Circle: Cycle speed")
        self.stdscr.addstr(8, 0, "Square: Play sound")
        self.stdscr.addstr(9, 0, "Triangle: Dock robot")
        self.stdscr.refresh()

    def draw_joystick(self, x_axis, y_axis):
        self.stdscr.addstr(11, 0, "Joystick X: [{:<20}] {:.2f} ".format("=" * int((x_axis + 1) * 10), x_axis))
        self.stdscr.addstr(12, 0, "Joystick Y: [{:<20}] {:.2f} ".format("=" * int((y_axis + 1) * 10), y_axis))
        self.stdscr.refresh()

async def poll_robot_battery(api: RobotAPI, update_callback):
    while True:
        battery = await api.get_battery()
        update_callback(battery)
        await asyncio.sleep(5)

async def joystick_loop(api: RobotAPI, joystick: JoystickController, state, exit_event: asyncio.Event):
    while not exit_event.is_set():
        x_axis, y_axis = joystick.poll()

        if joystick.button_pressed(0):  # X
            state['fan_state'] = joystick.cycle_fan()
            await api.set_fan(state['fan_state'])
            await asyncio.sleep(0.3)
        if joystick.button_pressed(1):  # CIRCLE
            state['speed_index'] = joystick.cycle_speed()
            await asyncio.sleep(0.3)
        if joystick.button_pressed(2):  # SQUARE
            await api.play_sound()
            await asyncio.sleep(0.3)
        if joystick.button_pressed(3):  # TRIANGLE
            await api.dock()
            await asyncio.sleep(0.3)
        if joystick.button_pressed(9):  # OPTIONS (Exit)
            exit_event.set()

        abs_x, abs_y = abs(x_axis), abs(y_axis)
        max_speed = SPEED_LEVELS[state['speed_index']]

        if abs_x < DEADZONE and abs_y < DEADZONE:
            await api.send_command(0.0, 0.0)
        elif abs_y > DEADZONE and abs_x < (DEADZONE * 1.5):
            velocity = ((abs_y - DEADZONE) / (1 - DEADZONE)) * max_speed
            velocity = velocity if y_axis > 0 else -velocity
            await api.send_command(clamp(velocity, -1.0, 1.0), 0.0)
        elif abs_x > DEADZONE and abs_y < (DEADZONE * 1.5):
            angle = 90 if x_axis > 0 else -90
            await api.send_command(0.0, angle)
        else:
            corrected_x = -x_axis if y_axis < 0 else x_axis
            angle_rad = math.atan2(corrected_x, y_axis)
            angle_deg = math.degrees(angle_rad)
            magnitude = math.sqrt(x_axis ** 2 + y_axis ** 2)
            velocity = ((max(0.0, magnitude - DEADZONE)) / (1 - DEADZONE)) * max_speed
            velocity = velocity if y_axis > 0 else -velocity
            await api.send_command(clamp(velocity, -1.0, 1.0), angle_deg)

        state['x_axis'], state['y_axis'] = x_axis, y_axis
        await asyncio.sleep(0.01)

async def tui_loop(tui: ValetudoTUI, state, exit_event: asyncio.Event):
    while not exit_event.is_set():
        tui.draw_labels(state['robot_battery'], state['speed_index'], state['fan_state'])
        tui.draw_joystick(state['x_axis'], state['y_axis'])
        await asyncio.sleep(0.1)

async def main(stdscr):
    state = {
        "robot_battery": "?",
        "speed_index": 1,
        "fan_state": "off",
        "x_axis": 0.0,
        "y_axis": 0.0,
    }
    exit_event = asyncio.Event()
    tui = ValetudoTUI(stdscr)
    try:
        joystick = JoystickController()
    except RuntimeError as e:
        stdscr.addstr(0, 0, str(e))
        stdscr.refresh()
        await asyncio.sleep(3)
        return
    async with aiohttp.ClientSession() as session:
        api = RobotAPI(session)
        # Callback to update battery in shared state
        def update_battery(val):
            state['robot_battery'] = val
        await asyncio.gather(
            poll_robot_battery(api, update_battery),
            joystick_loop(api, joystick, state, exit_event),
            tui_loop(tui, state, exit_event)
        )

if __name__ == "__main__":
    curses.wrapper(lambda stdscr: asyncio.run(main(stdscr)))