import aiohttp
import logging
import pygame
import os
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