from fleet.services.telemetry_service import TelemetryService


class AnomalyService:
    ANOMALY_THRESHOLD_PERCENT = 20.0
    RECENT_WINDOW_SIZE = 24
    MAX_ANOMALIES_RETURNED = 5

    def __init__(
        self,
        fleet_config: dict,
        telemetry_history: dict[str, list[dict]],
    ) -> None:
        self.fleet_config = fleet_config
        self.telemetry_history = telemetry_history

    def find_anomalous_devices(self) -> list[dict]:
        anomalies = []

        for device in self.fleet_config["devices"]:
            device_id = device["device_id"]
            readings = self.telemetry_history[device_id]

            historical_readings = readings[: self.RECENT_WINDOW_SIZE]
            recent_readings = readings[self.RECENT_WINDOW_SIZE :]

            if not historical_readings or not recent_readings:
                continue

            historical_average_power = TelemetryService.calculate_average_power(
                historical_readings
            )
            recent_average_power = TelemetryService.calculate_average_power(recent_readings)

            percent_increase = (
                (recent_average_power - historical_average_power) / historical_average_power
            ) * 100

            if percent_increase > self.ANOMALY_THRESHOLD_PERCENT:
                anomalies.append({
                    "device_id": device_id,
                    "name": device["name"],
                    "location": device["location"],
                    "historical_average_power_watts": round(historical_average_power, 2),
                    "recent_average_power_watts": round(recent_average_power, 2),
                    "percent_increase": round(percent_increase, 1),
                })

        anomalies.sort(key=lambda anomaly: anomaly["percent_increase"], reverse=True)
        return anomalies

    def build_anomaly_response(self, anomalies: list[dict]) -> dict:
        total_devices = len(self.fleet_config["devices"])

        if not anomalies:
            return {
                "status": "all_normal",
                "summary": f"All {total_devices} devices are operating within normal parameters.",
                "anomaly_count": 0,
                "anomalies": [],
            }

        worst = anomalies[0]
        capped_anomalies = anomalies[: self.MAX_ANOMALIES_RETURNED]
        truncated = len(anomalies) > self.MAX_ANOMALIES_RETURNED

        summary = (
            f"{len(anomalies)} of {total_devices} devices anomalous, "
            f"worst: {worst['device_id']} (+{worst['percent_increase']}%)"
        )
        if truncated:
            summary += f". Showing top {self.MAX_ANOMALIES_RETURNED} by severity."

        return {
            "status": "anomalies_detected",
            "summary": summary,
            "anomaly_count": len(anomalies),
            "truncated": truncated,
            "anomalies": capped_anomalies,
        }
