import json
from datetime import datetime, timezone

import pytest

from fleet.validation.exceptions import InvalidDeviceIdError


class TestFleetConfigResource:
    def test_returns_valid_compact_json(self, server):
        result = server.fleet_config_resource()
        parsed = json.loads(result)
        assert parsed == server.fleet_config
        assert "\n" not in result


class TestTelemetry:
    def test_get_latest_telemetry_for_valid_device(self, server):
        result = server.telemetry_service.get_latest_telemetry("DEV-001")
        assert result["device_id"] == "DEV-001"
        assert "power_watts" in result
        assert result["power_watts"] == round(result["voltage"] * result["current"], 2)

    def test_get_device_telemetry_tool(self, server):
        result = server.get_device_telemetry("DEV-001")
        assert "error" not in result
        assert result["device_id"] == "DEV-001"


class TestDeviceIdValidation:
    @pytest.mark.parametrize(
        "malicious_device_id",
        [
            "DEV-001'; DROP TABLE devices;--",
            "../../etc/passwd",
            "<script>alert(1)</script>",
            "DEV-999",
            "",
            "DEV-99999",
        ],
    )
    def test_rejects_malicious_or_invalid_device_ids(self, server, malicious_device_id):
        with pytest.raises(InvalidDeviceIdError):
            server.device_validator.validate(malicious_device_id)

    def test_tool_returns_error_for_invalid_id(self, server):
        result = server.get_device_telemetry("'; DROP TABLE--")
        assert "error" in result

    def test_reboot_tool_returns_error_for_invalid_id(self, server):
        result = server.reboot_device("not-a-device")
        assert "error" in result


class TestAnomalyDetection:
    def test_detects_dev_002_and_dev_004_as_anomalies(self, server):
        anomalies = server.anomaly_service.find_anomalous_devices()
        anomaly_device_ids = {anomaly["device_id"] for anomaly in anomalies}
        assert "DEV-002" in anomaly_device_ids
        assert "DEV-004" in anomaly_device_ids

    def test_build_anomaly_response(self, server):
        anomalies = server.anomaly_service.find_anomalous_devices()
        response = server.anomaly_service.build_anomaly_response(anomalies)
        assert response["status"] == "anomalies_detected"
        assert response["anomaly_count"] == 2

    def test_calculate_efficiency_anomalies_tool(self, server):
        result = server.calculate_efficiency_anomalies()
        assert result["status"] == "anomalies_detected"
        assert result["anomaly_count"] == 2


class TestReboot:
    def test_rejects_healthy_device(self, server):
        result = server.reboot_service.execute_reboot("DEV-001")
        assert result["status"] == "reboot_rejected"
        assert "normal parameters" in result["error"]

    def test_succeeds_for_anomalous_device(self, server):
        result = server.reboot_service.execute_reboot("DEV-002")
        assert result["status"] == "reboot_command_sent"

    def test_cooldown_blocks_repeat_reboot(self, server):
        first_result = server.reboot_service.execute_reboot("DEV-002")
        assert first_result["status"] == "reboot_command_sent"

        second_result = server.reboot_service.execute_reboot("DEV-002")
        assert second_result["status"] == "reboot_rejected"
        assert "recently" in second_result["error"]

    def test_reboot_tool_enforces_cooldown(self, server):
        first_result = server.reboot_device("DEV-004")
        assert first_result["status"] == "reboot_command_sent"

        server.reboot_service._reboot_timestamps["DEV-004"] = datetime.now(timezone.utc)
        second_result = server.reboot_device("DEV-004")
        assert second_result["status"] == "reboot_rejected"
