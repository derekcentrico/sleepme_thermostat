import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, MANUFACTURER, SCHEDULE_SWITCH_NAME
from .sleepme import SleepMeClient
from .update_manager import SleepMeUpdateManager

_LOGGER = logging.getLogger(__name__)

COMMAND_REFRESH_DELAY_S = 5


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SleepMe switch entities."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    update_manager = entry_data["update_manager"]
    client = entry_data["client"]
    device_info_data = entry_data["device_info"]

    async_add_entities(
        [
            SleepMeScheduleSwitch(
                update_manager, client, device_info_data
            )
        ]
    )


class SleepMeScheduleSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a SleepMe schedule switch."""

    def __init__(self, coordinator: SleepMeUpdateManager, client: SleepMeClient, device_info_data: dict):
        """Initialize the switch."""
        super().__init__(coordinator)
        self.client = client
        
        display_name = device_info_data["display_name"]

        self._attr_name = f"{display_name} {SCHEDULE_SWITCH_NAME}"
        self._attr_unique_id = f"{client.device_id}_schedule_switch"

        self._attr_device_info = {
            "identifiers": {(DOMAIN, client.device_id)},
            "name": display_name,
            "manufacturer": MANUFACTURER,
            "model": device_info_data.get("model"),
            "sw_version": device_info_data.get("firmware_version"),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the schedule is enabled."""
        if self.coordinator.data and (control := self.coordinator.data.get("control", {})):
            return control.get("has_schedule_enabled", False)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the device schedule on."""
        if await self.client.set_schedule_enabled(True):
            if self.coordinator.data and "control" in self.coordinator.data:
                self.coordinator.data["control"]["has_schedule_enabled"] = True
                self.async_write_ha_state()
            async_call_later(self.hass, COMMAND_REFRESH_DELAY_S, self.coordinator.async_request_refresh)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the device schedule off."""
        if await self.client.set_schedule_enabled(False):
            if self.coordinator.data and "control" in self.coordinator.data:
                self.coordinator.data["control"]["has_schedule_enabled"] = False
                self.async_write_ha_state()
            async_call_later(self.hass, COMMAND_REFRESH_DELAY_S, self.coordinator.async_request_refresh)