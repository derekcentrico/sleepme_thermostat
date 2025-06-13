import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .sleepme import SleepMeClient
from .update_manager import SleepMeUpdateManager

_LOGGER = logging.getLogger(__name__)

WATER_LOW_THRESHOLD = 20


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SleepMe binary sensor entities."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    update_manager = entry_data["update_manager"]
    client = entry_data["client"]
    device_info_data = entry_data["device_info"]

    async_add_entities(
        [
            SleepMeWaterLevelBinarySensor(
                update_manager, client, device_info_data
            )
        ]
    )


class SleepMeWaterLevelBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a SleepMe water level binary sensor."""

    def __init__(self, coordinator: SleepMeUpdateManager, client: SleepMeClient, device_info_data: dict):
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        
        display_name = device_info_data["display_name"]
        
        self._attr_name = f"{display_name} Water Low"
        self._attr_unique_id = f"{client.device_id}_water_low"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM

        self._attr_device_info = {
            "identifiers": {(DOMAIN, client.device_id)},
            "name": display_name,
            "manufacturer": MANUFACTURER,
            "model": device_info_data.get("model"),
            "sw_version": device_info_data.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the water level is low."""
        if self.coordinator.data and (status := self.coordinator.data.get("status", {})):
            water_level = status.get("water_level_percent", 100)
            return water_level < WATER_LOW_THRESHOLD
        return False