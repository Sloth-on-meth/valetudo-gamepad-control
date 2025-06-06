import os
import asyncio
import aiohttp
import curses
import pygame
import math
import json
import logging
from typing import Optional
from robot_api import RobotAPI
from joystick_controller import JoystickController
from tui import ValetudoTUI
from config import (
    VALETUDO_URL, SPEED_LEVELS, DEADZONE,
    ANGLE_EPSILON, VELOCITY_EPSILON, SEND_INTERVAL_MS
)


logging.basicConfig(level=logging.INFO)

def clamp(val: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(val, max_val))


async def poll_robot_battery(api: RobotAPI, update_callback):
    while True:
        battery = await api.get_battery()
        update_callback(battery)
        await asyncio.sleep(5)

def calculate_movement(x_axis, y_axis, max_speed):
    """Calculate velocity and angle based on joystick position.
    
    Args:
        x_axis: Joystick X axis position (-1 to 1)
        y_axis: Joystick Y axis position (-1 to 1)
        max_speed: Maximum speed factor
        
    Returns:
        tuple: (velocity, angle_deg)
    """
    abs_x, abs_y = abs(x_axis), abs(y_axis)
    
    # Deadzone - No movement
    if abs_x < DEADZONE and abs_y < DEADZONE:
        return 0.0, 0.0
    
    # Mostly vertical movement
    if abs_y > DEADZONE and abs_x < (DEADZONE * 1.5):
        velocity = normalize_axis_value(abs_y) * max_speed
        velocity = velocity if y_axis > 0 else -velocity
        return clamp(velocity, -1.0, 1.0), 0.0
    
    # Mostly horizontal movement - pure rotation
    if abs_x > DEADZONE and abs_y < (DEADZONE * 1.5):
        angle = 90 if x_axis > 0 else -90
        return 0.0, angle
    
    # Combined movement - both velocity and angle
    corrected_x = -x_axis if y_axis < 0 else x_axis
    angle_deg = math.degrees(math.atan2(corrected_x, y_axis))
    
    magnitude = math.sqrt(x_axis ** 2 + y_axis ** 2)
    velocity = normalize_axis_value(magnitude) * max_speed
    velocity = velocity if y_axis > 0 else -velocity
    
    return clamp(velocity, -1.0, 1.0), angle_deg


def normalize_axis_value(value):
    """Normalize joystick axis value accounting for deadzone."""
    return (max(0.0, value - DEADZONE)) / (1 - DEADZONE)


async def joystick_loop(api: RobotAPI, joystick: JoystickController, state, exit_event: asyncio.Event):
    while not exit_event.is_set():
        # Get joystick input
        x_axis, y_axis = joystick.poll()

        # Handle button presses
        if joystick.button_pressed(0):  # X
            state['fan_state'] = joystick.cycle_fan()
            await api.set_fan(state['fan_state'])
            await asyncio.sleep(0.3)
        if joystick.button_pressed(1):  # CIRCLE
            state['speed_index'] = joystick.cycle_speed()
            await asyncio.sleep(0.3)
        if joystick.button_pressed(3):  # SQUARE
            await api.play_sound()
            await asyncio.sleep(0.3)
        if joystick.button_pressed(2):  # TRIANGLE
            await api.dock()
            exit_event.set()
            await asyncio.sleep(0.3)
        if joystick.button_pressed(9):  # OPTIONS (Exit)
            exit_event.set()

        # Calculate and send movement commands
        max_speed = SPEED_LEVELS[state['speed_index']]
        velocity, angle = calculate_movement(x_axis, y_axis, max_speed)
        await api.send_command(velocity, angle)

        # Update state for UI display
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