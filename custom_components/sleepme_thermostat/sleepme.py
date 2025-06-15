import logging
import aiohttp
from .sleepme_api import SleepMeAPI

_LOGGER = logging.getLogger(__name__)

class SleepMeClient:
    """A client for interacting with SleepMe devices."""

    def __init__(self, session: aiohttp.ClientSession, api_url, token, device_id):
        """Initialize the client."""
        self._api = SleepMeAPI(session, api_url, token, device_id)
        self.device_id = device_id

    async def patch_command(self, payload: dict) -> bool:
        """Send a generic command payload."""
        _LOGGER.debug(f"[Device {self.device_id}] Sending command payload: {payload}")
        response = await self._api.patch_device_control(payload)
        return response is not None

    async def get_all_devices(self):
        """Get a list of all devices from the API."""
        return await self._api.get_all_devices()

    async def get_device_status(self):
        """Get the full status of the device."""
        return await self._api.get_device_status()
    
    async def set_temperature(self, temperature_c: float) -> bool:
        """Set the target temperature of the device in Celsius."""
        rounded_temp = round(temperature_c, 1)
        return await self.patch_command({"set_temperature_c": rounded_temp})

    async def set_power_status(self, is_active: bool) -> bool:
        """Set the power status of the device."""
        target_status = "active" if is_active else "standby"
        return await self.patch_command({"thermal_control_status": target_status})

    async def set_schedule_enabled(self, enabled: bool) -> bool:
        """Enable or disable the device's internal schedule."""
        return await self.patch_command({"has_schedule_enabled": enabled})

    async def set_display_brightness(self, brightness_percent: int) -> bool:
        """Set the display brightness."""
        return await self.patch_command({"brightness_level_percent": brightness_percent})