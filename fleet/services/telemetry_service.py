
class TelemetryService:
    def __init__(self, telemetry_history: dict[str, list[dict]]) -> None:
        self.telemetry_history = telemetry_history

    def get_latest_telemetry(self, device_id: str) -> dict:
        readings = self.telemetry_history[device_id]
        latest = readings[-1]
        power_watts = round(latest["voltage"] * latest["current"], 2)

        return {
            "device_id": device_id,
            "timestamp": latest["timestamp"],
            "voltage": latest["voltage"],
            "current": latest["current"],
            "temperature": latest["temperature"],
            "power_watts": power_watts,
        }

    @staticmethod
    def calculate_average_power(readings: list[dict]) -> float:
        total_power = sum(reading["voltage"] * reading["current"] for reading in readings)
        return total_power / len(readings)
