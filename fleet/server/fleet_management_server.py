import json

from mcp.server.fastmcp import FastMCP

from fleet.data.fleet_data import FLEET_CONFIG, TELEMETRY_HISTORY, VALID_DEVICE_IDS
from fleet.services.anomaly_service import AnomalyService
from fleet.services.reboot_service import RebootService
from fleet.services.telemetry_service import TelemetryService
from fleet.validation.device_validator import DeviceValidator
from fleet.validation.exceptions import InvalidDeviceIdError


class FleetManagementServer:
    def __init__(self) -> None:
        self.fleet_config = FLEET_CONFIG
        self.device_validator = DeviceValidator(VALID_DEVICE_IDS)
        self.telemetry_service = TelemetryService(TELEMETRY_HISTORY)
        self.anomaly_service = AnomalyService(self.fleet_config, TELEMETRY_HISTORY)
        self.reboot_service = RebootService(
            self.fleet_config["reboot_cooldown_seconds"],
            self.anomaly_service,
        )
        self.mcp = FastMCP("Fleet Management Server")
        self._register_resources()
        self._register_tools()

    def _register_resources(self) -> None:
        fleet_config = self.fleet_config

        @self.mcp.resource("devices://fleet-config")
        def fleet_config_resource() -> str:
            return json.dumps(fleet_config)

        self.fleet_config_resource = fleet_config_resource

    def _register_tools(self) -> None:
        device_validator = self.device_validator
        telemetry_service = self.telemetry_service
        anomaly_service = self.anomaly_service
        reboot_service = self.reboot_service

        @self.mcp.tool()
        def get_device_telemetry(device_id: str) -> dict:
            """Returns the latest telemetry reading for a given device: voltage, current, temperature, and power."""
            try:
                validated_device_id = device_validator.validate(device_id)
            except InvalidDeviceIdError as error:
                return {"error": str(error)}

            return telemetry_service.get_latest_telemetry(validated_device_id)

        @self.mcp.tool()
        def calculate_efficiency_anomalies() -> dict:
            """Compares each device's recent 24-hour power consumption against its historical baseline and returns anomalous devices."""
            anomalies = anomaly_service.find_anomalous_devices()
            return anomaly_service.build_anomaly_response(anomalies)

        @self.mcp.tool()
        def reboot_device(device_id: str) -> dict:
            """Sends a reboot command to an anomalous device only. Rejects healthy devices and enforces a per-device cooldown."""
            try:
                validated_device_id = device_validator.validate(device_id)
            except InvalidDeviceIdError as error:
                return {"error": str(error)}

            return reboot_service.execute_reboot(validated_device_id)

        self.get_device_telemetry = get_device_telemetry
        self.calculate_efficiency_anomalies = calculate_efficiency_anomalies
        self.reboot_device = reboot_device
