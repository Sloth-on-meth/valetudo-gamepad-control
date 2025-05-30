import aiohttp
import logging
from typing import Optional
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