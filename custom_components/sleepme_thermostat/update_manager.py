import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .sleepme import SleepMeClient

_LOGGER = logging.getLogger(__name__)

COMMAND_REFRESH_DELAY_S = 5


class SleepMeUpdateManager(DataUpdateCoordinator):
    """Manages data updates for SleepMe devices."""

    def __init__(self, hass: HomeAssistant, client: SleepMeClient):
        """Initialize the update manager."""
        self.client = client
        
        update_interval = timedelta(seconds=60)

        super().__init__(
            hass,
            _LOGGER,
            name=f"SleepMe Update Manager {client.device_id}",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch the latest data from the SleepMe API."""
        try:
            device_status = await self.client.get_device_status()
            _LOGGER.debug("Received device status response: %s", device_status)

            if not device_status or not isinstance(device_status, dict):
                raise UpdateFailed(f"API returned an invalid or empty response: {device_status}")

            if "status" not in device_status or "control" not in device_status:
                raise UpdateFailed(f"API response missing essential keys 'status' or 'control': {device_status}")

            return {
                "status": device_status.get("status", {}),
                "control": device_status.get("control", {}),
                "about": device_status.get("about", {}),
            }
        except Exception as err:
            _LOGGER.error("An unexpected error occurred during status update: %s", err)
            raise UpdateFailed(f"Error during status update: {err}") from err