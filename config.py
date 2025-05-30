import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

with open(CONFIG_PATH) as f:
    config = json.load(f)

VALETUDO_URL = config["valetudo_url"]
SPEED_LEVELS = config["speed_levels"]
DEADZONE = config["deadzone"]
ANGLE_EPSILON = config.get("angle_epsilon", 1.0)
VELOCITY_EPSILON = config.get("velocity_epsilon", 0.01)
SEND_INTERVAL_MS = config.get("send_interval_ms", 100)