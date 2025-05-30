import aiohttp
import logging
import pygame
import os
# Configuration
import json
import os

with open(os.path.join(os.path.dirname(__file__), 'config.json')) as f:
    config = json.load(f)
VALETUDO_URL = config["valetudo_url"]
SPEED_LEVELS = config["speed_levels"]
DEADZONE = config["deadzone"]

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
        self.speed_index = (self.speed_index + 1) % len(speed_levels)
        return self.speed_index

    def cycle_fan(self):
        self.fan_index = (self.fan_index + 1) % len(fan_states)
        return fan_states[self.fan_index]