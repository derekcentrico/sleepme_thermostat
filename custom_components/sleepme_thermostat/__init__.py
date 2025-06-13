import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client
from .sleepme import SleepMeClient
from .update_manager import SleepMeUpdateManager
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "binary_sensor", "sensor", "switch"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the SleepMe Thermostat component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up SleepMe Thermostat from a config entry."""
    hass.data[DOMAIN].setdefault(entry.entry_id, {})
    
    api_url = entry.data["api_url"]
    api_token = entry.data["api_token"]
    device_id = entry.data["device_id"]
    display_name = entry.data["display_name"]

    session = aiohttp_client.async_get_clientsession(hass)
    
    client = SleepMeClient(session, api_url, api_token, device_id)
    hass.data[DOMAIN][entry.entry_id]["client"] = client

    update_manager = SleepMeUpdateManager(hass, client)
    hass.data[DOMAIN][entry.entry_id]["update_manager"] = update_manager

    await update_manager.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id]["device_info"] = {
        "firmware_version": entry.data.get("firmware_version"),
        "mac_address": entry.data.get("mac_address"),
        "model": entry.data.get("model"),
        "serial_number": entry.data.get("serial_number"),
        "display_name": display_name,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("SleepMe Thermostat component for %s initialized successfully.", display_name)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok