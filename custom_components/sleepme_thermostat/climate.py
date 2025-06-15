import logging
from typing import Any

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, HVAC_ACTION_COOLING, HVAC_ACTION_HEATING, HVAC_ACTION_IDLE,
    HVAC_ACTION_OFF, HVAC_MODES, MANUFACTURER, PRESET_PRECONDITIONING, SUPPORT_FLAGS
)
from .sleepme import SleepMeClient
from .update_manager import SleepMeUpdateManager
from .debouncer import Debouncer

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SleepMe climate entities from a config entry."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    update_manager = entry_data["update_manager"]
    client = entry_data["client"]
    device_info_data = entry_data["device_info"]
    async_add_entities([SleepMeClimateEntity(update_manager, client, device_info_data)])

class SleepMeClimateEntity(CoordinatorEntity, ClimateEntity):
    """Representation of a SleepMe climate entity."""

    def __init__(
        self,
        coordinator: SleepMeUpdateManager,
        client: SleepMeClient,
        device_info_data: dict,
    ):
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self.client = client
        
        self._pending_payload = {}
        self._command_debouncer = Debouncer(
            self.hass, 2.0, self._async_send_commands
        )
        
        display_name = device_info_data["display_name"]
        
        self._attr_name = display_name
        self._attr_unique_id = f"{client.device_id}_climate"
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_hvac_modes = HVAC_MODES
        self._attr_supported_features = SUPPORT_FLAGS
        self._attr_preset_modes = [PRESET_PRECONDITIONING]

        self._attr_device_info = {
            "identifiers": {(DOMAIN, client.device_id)},
            "name": display_name, "manufacturer": MANUFACTURER,
            "model": device_info_data.get("model"), "sw_version": device_info_data.get("firmware_version"),
        }

    @property
    def hvac_mode(self):
        if not self.coordinator.data: return HVACMode.OFF
        control = self.coordinator.data.get("control", {})
        thermal_status = control.get("thermal_control_status")
        if thermal_status in ["active", "preconditioning"]:
            set_temp = control.get("set_temperature_c")
            current_temp = self.coordinator.data.get("status", {}).get("water_temperature_c")
            if set_temp is not None and current_temp is not None:
                return HVACMode.COOL if set_temp < current_temp else HVACMode.HEAT
            return HVACMode.COOL
        return HVACMode.OFF

    @property
    def hvac_action(self):
        if not self.coordinator.data: return HVAC_ACTION_OFF
        control = self.coordinator.data.get("control", {})
        status = self.coordinator.data.get("status", {})
        thermal_status = control.get("thermal_control_status")
        if thermal_status in ["active", "preconditioning"]:
            set_temp = control.get("set_temperature_c")
            current_temp = status.get("water_temperature_c")
            if set_temp is not None and current_temp is not None:
                if set_temp < current_temp: return HVAC_ACTION_COOLING
                if set_temp > current_temp: return HVAC_ACTION_HEATING
                return HVAC_ACTION_IDLE
            return HVAC_ACTION_COOLING
        return HVAC_ACTION_OFF

    @property
    def preset_mode(self):
        if self.coordinator.data and (control := self.coordinator.data.get("control", {})):
            if control.get("thermal_control_status") == "preconditioning": return PRESET_PRECONDITIONING
        return None

    @property
    def current_temperature(self):
        if self.coordinator.data and (status := self.coordinator.data.get("status", {})):
            return status.get("water_temperature_c")
        return None

    @property
    def target_temperature(self):
        if self.coordinator.data and (control := self.coordinator.data.get("control", {})):
            return control.get("set_temperature_c")
        return None

    async def _async_send_commands(self):
        """Send the debounced command payload to the API."""
        if not self._pending_payload:
            return

        payload_to_send = self._pending_payload.copy()
        self._pending_payload.clear()

        if await self.client.patch_command(payload_to_send):
            await self.coordinator.async_request_refresh()

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set a new target temperature."""
        temperature_c = kwargs.get(ATTR_TEMPERATURE)
        if temperature_c is None: return

        if self.coordinator.data and "control" in self.coordinator.data:
            self.coordinator.data["control"]["set_temperature_c"] = temperature_c
            self.async_write_ha_state()
        
        self._pending_payload["set_temperature_c"] = round(temperature_c, 1)
        self._command_debouncer.async_schedule()

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set a new HVAC mode."""
        is_active = hvac_mode in [HVACMode.COOL, HVACMode.HEAT]
        
        if self.coordinator.data and "control" in self.coordinator.data:
            self.coordinator.data["control"]["thermal_control_status"] = "active" if is_active else "standby"
            self.async_write_ha_state()

        self._pending_payload["thermal_control_status"] = "active" if is_active else "standby"
        self._command_debouncer.async_schedule()