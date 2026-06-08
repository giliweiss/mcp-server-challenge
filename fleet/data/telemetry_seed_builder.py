from datetime import datetime, timezone


class TelemetrySeedBuilder:
    @staticmethod
    def build_hourly_readings(
        base_voltage: float,
        base_current: float,
        base_temperature: float,
        anomaly_start_hour: int | None = None,
        anomaly_factor: float = 1.0,
    ) -> list[dict]:
        readings = []
        base_timestamp = datetime(2026, 6, 6, 0, 0, 0, tzinfo=timezone.utc)

        for hour in range(48):
            timestamp = base_timestamp.replace(hour=hour % 24)

            factor = (
                anomaly_factor
                if anomaly_start_hour is not None and hour >= anomaly_start_hour
                else 1.0
            )

            readings.append({
                "timestamp": timestamp.isoformat(),
                "voltage": round(base_voltage * factor + (hour % 3) * 0.1, 2),
                "current": round(base_current * factor + (hour % 5) * 0.05, 2),
                "temperature": round(base_temperature * factor + (hour % 4) * 0.2, 2),
            })

        return readings

    @staticmethod
    def build_all() -> dict[str, list[dict]]:
        return {
            "DEV-001": TelemetrySeedBuilder.build_hourly_readings(
                base_voltage=220.0,
                base_current=10.5,
                base_temperature=65.0,
            ),
            "DEV-002": TelemetrySeedBuilder.build_hourly_readings(
                base_voltage=218.5,
                base_current=11.0,
                base_temperature=70.0,
                anomaly_start_hour=24,
                anomaly_factor=1.35,
            ),
            "DEV-003": TelemetrySeedBuilder.build_hourly_readings(
                base_voltage=221.0,
                base_current=9.8,
                base_temperature=63.0,
            ),
            "DEV-004": TelemetrySeedBuilder.build_hourly_readings(
                base_voltage=219.0,
                base_current=10.2,
                base_temperature=68.0,
                anomaly_start_hour=24,
                anomaly_factor=1.42,
            ),
            "DEV-005": TelemetrySeedBuilder.build_hourly_readings(
                base_voltage=220.5,
                base_current=10.0,
                base_temperature=66.0,
            ),
        }
