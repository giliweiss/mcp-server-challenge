import re

from fleet.validation.exceptions import InvalidDeviceIdError


class DeviceValidator:
    DEVICE_ID_PATTERN = re.compile(r"DEV-\d{3}")
    MAX_DEVICE_ID_LENGTH = 20

    def __init__(self, valid_device_ids: set[str]) -> None:
        self.valid_device_ids = valid_device_ids

    def validate(self, device_id: str) -> str:
        if not isinstance(device_id, str):
            raise InvalidDeviceIdError("device_id must be a string")

        stripped = device_id.strip()

        if not stripped:
            raise InvalidDeviceIdError("device_id cannot be empty")

        if len(stripped) > self.MAX_DEVICE_ID_LENGTH:
            raise InvalidDeviceIdError("device_id is too long")

        if not self.DEVICE_ID_PATTERN.fullmatch(stripped):
            raise InvalidDeviceIdError(
                "device_id has an invalid format. Expected format: DEV-XXX (e.g. DEV-001)"
            )

        if stripped not in self.valid_device_ids:
            raise InvalidDeviceIdError("device_id does not exist in the fleet")

        return stripped
