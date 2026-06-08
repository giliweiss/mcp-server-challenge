from datetime import datetime, timezone

from fleet.services.anomaly_service import AnomalyService


class RebootService:
    def __init__(self, reboot_cooldown_seconds: int, anomaly_service: AnomalyService) -> None:
        self.reboot_cooldown_seconds = reboot_cooldown_seconds
        self.anomaly_service = anomaly_service
        self._reboot_timestamps: dict[str, datetime] = {}

    def clear_reboot_timestamps(self) -> None:
        self._reboot_timestamps.clear()

    def execute_reboot(self, device_id: str) -> dict:
        anomalous_device_ids = {
            anomaly["device_id"] for anomaly in self.anomaly_service.find_anomalous_devices()
        }

        if device_id not in anomalous_device_ids:
            return {
                "device_id": device_id,
                "status": "reboot_rejected",
                "error": "Device is operating within normal parameters. Reboot is only allowed for anomalous devices.",
            }

        last_reboot = self._reboot_timestamps.get(device_id)

        if last_reboot is not None:
            elapsed_seconds = (datetime.now(timezone.utc) - last_reboot).total_seconds()
            if elapsed_seconds < self.reboot_cooldown_seconds:
                remaining_seconds = int(self.reboot_cooldown_seconds - elapsed_seconds)
                return {
                    "device_id": device_id,
                    "status": "reboot_rejected",
                    "error": f"Device was rebooted recently. Try again in {remaining_seconds} seconds.",
                }

        self._reboot_timestamps[device_id] = datetime.now(timezone.utc)

        return {
            "device_id": device_id,
            "status": "reboot_command_sent",
            "message": f"Reboot command successfully dispatched to {device_id}. Device will restart within 30 seconds.",
        }
