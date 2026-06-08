import pytest

from fleet.server.fleet_management_server import FleetManagementServer


@pytest.fixture
def server() -> FleetManagementServer:
    fleet_server = FleetManagementServer()
    fleet_server.reboot_service.clear_reboot_timestamps()
    yield fleet_server
    fleet_server.reboot_service.clear_reboot_timestamps()
