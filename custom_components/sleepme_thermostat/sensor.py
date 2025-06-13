import logging

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .sleepme import SleepMeClient
from .update_manager import SleepMeUpdateManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SleepMe sensor entities."""
    entry_data = hass.data[DOMAIN][config_entry.entry_id]
    update_manager = entry_data["update_manager"]
    client = entry_data["client"]
    device_info_data = entry_data["device_info"]

    sensors = [
        SleepMeWaterLevelPercentSensor(update_manager, client, device_info_data),
        SleepMeSetTemperatureSensor(update_manager, client, device_info_data),
        SleepMeCurrentTemperatureSensor(update_manager, client, device_info_data),
    ]
    async_add_entities(sensors)


class BaseSleepMeSensor(CoordinatorEntity, SensorEntity):
    """Base class for SleepMe sensors."""

    def __init__(self, coordinator: SleepMeUpdateManager, client: SleepMeClient, device_info_data: dict, sensor_name: str, unique_id_suffix: str):
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        display_name = device_info_data["display_name"]
        
        self._attr_name = f"{display_name} {sensor_name}"
        self._attr_unique_id = f"{client.device_id}_{unique_id_suffix}"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, client.device_id)},
            "name": display_name,
            "manufacturer": MANUFACTURER,
            "model": device_info_data.get("model"),
            "sw_version": device_info_data.get("firmware_version"),
        }


class SleepMeWaterLevelPercentSensor(BaseSleepMeSensor):
    """Representation of the water level percentage sensor."""

    def __init__(self, coordinator: SleepMeUpdateManager, client: SleepMeClient, device_info_data: dict):
        """Initialize the sensor."""
        super().__init__(coordinator, client, device_info_data, "Water Level", "water_level_percent")
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_icon = "mdi:water-percent"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and (status := self.coordinator.data.get("status", {})):
            return status.get("water_level")
        return None


class SleepMeSetTemperatureSensor(BaseSleepMeSensor):
    """Representation of the set temperature sensor."""

    def __init__(self, coordinator: SleepMeUpdateManager, client: SleepMeClient, device_info_data: dict):
        """Initialize the sensor."""
        super().__init__(coordinator, client, device_info_data, "Set Temperature", "set_temp")
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and (control := self.coordinator.data.get("control", {})):
            return control.get("set_temperature_c")
        return None


class SleepMeCurrentTemperatureSensor(BaseSleepMeSensor):
    """Representation of the current temperature sensor."""

    def __init__(self, coordinator: SleepMeUpdateManager, client: SleepMeClient, device_info_data: dict):
        """Initialize the sensor."""
        super().__init__(coordinator, client, device_info_data, "Current Temperature", "current_temp")
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.coordinator.data and (status := self.coordinator.data.get("status", {})):
            return status.get("water_temperature_c")
        return None