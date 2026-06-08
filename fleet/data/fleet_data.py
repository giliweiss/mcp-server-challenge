import json
from pathlib import Path

from fleet.data.telemetry_seed_builder import TelemetrySeedBuilder

FLEET_CONFIG_PATH = Path(__file__).parent / "fleet_config.json"


def load_fleet_config() -> dict:
    with FLEET_CONFIG_PATH.open(encoding="utf-8") as config_file:
        return json.load(config_file)


FLEET_CONFIG = load_fleet_config()
VALID_DEVICE_IDS = {device["device_id"] for device in FLEET_CONFIG["devices"]}
TELEMETRY_HISTORY = TelemetrySeedBuilder.build_all()
