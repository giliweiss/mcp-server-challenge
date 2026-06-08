import json

import pytest

from main import mcp, server

PART_A_TOOLS = {
    "get_device_telemetry",
    "calculate_efficiency_anomalies",
    "reboot_device",
}
FLEET_CONFIG_URI = "devices://fleet-config"
REQUIRED_TELEMETRY_FIELDS = {"device_id", "timestamp", "voltage", "current", "temperature"}


def parse_tool_result(tool_result: list) -> dict:
    return json.loads(tool_result[0].text)


@pytest.mark.anyio
class TestPartAMcpRegistration:
    async def test_registers_all_part_a_tools(self):
        tool_names = {tool.name for tool in await mcp.list_tools()}
        assert PART_A_TOOLS.issubset(tool_names)

    async def test_registers_fleet_config_resource(self):
        resource_uris = {str(resource.uri) for resource in await mcp.list_resources()}
        assert FLEET_CONFIG_URI in resource_uris


@pytest.mark.anyio
class TestPartAFleetConfigResource:
    async def test_read_resource_returns_fleet_config(self):
        contents = await mcp.read_resource(FLEET_CONFIG_URI)
        parsed = json.loads(contents[0].content)

        assert parsed["fleet_name"] == "Alpha Industrial Fleet"
        assert len(parsed["devices"]) == 5
        assert parsed == server.fleet_config

    def test_resource_handler_returns_compact_json(self):
        result = server.fleet_config_resource()
        parsed = json.loads(result)
        assert parsed == server.fleet_config
        assert "\n" not in result


@pytest.mark.anyio
class TestPartAGetDeviceTelemetry:
    async def test_returns_required_telemetry_fields(self):
        result = parse_tool_result(
            await mcp.call_tool("get_device_telemetry", {"device_id": "DEV-001"})
        )

        assert REQUIRED_TELEMETRY_FIELDS.issubset(result.keys())
        assert result["device_id"] == "DEV-001"
        assert result["power_watts"] == round(result["voltage"] * result["current"], 2)

    async def test_returns_error_for_invalid_device_id(self):
        result = parse_tool_result(
            await mcp.call_tool("get_device_telemetry", {"device_id": "DEV-999"})
        )
        assert "error" in result


@pytest.mark.anyio
class TestPartACalculateEfficiencyAnomalies:
    async def test_detects_expected_anomalies(self):
        result = parse_tool_result(
            await mcp.call_tool("calculate_efficiency_anomalies", {})
        )

        assert result["status"] == "anomalies_detected"
        assert result["anomaly_count"] == 2

        anomaly_device_ids = {anomaly["device_id"] for anomaly in result["anomalies"]}
        assert anomaly_device_ids == {"DEV-002", "DEV-004"}

    async def test_anomaly_entries_include_comparison_fields(self):
        result = parse_tool_result(
            await mcp.call_tool("calculate_efficiency_anomalies", {})
        )
        first_anomaly = result["anomalies"][0]

        assert "historical_average_power_watts" in first_anomaly
        assert "recent_average_power_watts" in first_anomaly
        assert "percent_increase" in first_anomaly
        assert first_anomaly["percent_increase"] > 20


@pytest.mark.anyio
class TestPartARebootDevice:
    async def test_rejects_healthy_device(self):
        result = parse_tool_result(
            await mcp.call_tool("reboot_device", {"device_id": "DEV-001"})
        )

        assert result["status"] == "reboot_rejected"
        assert "error" in result

    async def test_accepts_anomalous_device(self):
        result = parse_tool_result(
            await mcp.call_tool("reboot_device", {"device_id": "DEV-002"})
        )

        assert result["status"] == "reboot_command_sent"
        assert "message" in result

    async def test_returns_error_for_invalid_device_id(self):
        result = parse_tool_result(
            await mcp.call_tool("reboot_device", {"device_id": "not-valid"})
        )
        assert "error" in result
