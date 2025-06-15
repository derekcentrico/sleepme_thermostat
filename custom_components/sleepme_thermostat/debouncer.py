import asyncio
from typing import Coroutine, Any, Callable
from homeassistant.core import HomeAssistant

class Debouncer:
    """Class to debounce calls to a coroutine."""

    def __init__(self, hass: HomeAssistant, seconds: float, function: Callable[..., Coroutine[Any, Any, None]]):
        """Initialize the debouncer."""
        self.hass = hass
        self.seconds = seconds
        self.function = function
        self._task = None

    def async_schedule(self):
        """Schedule the call to the function."""
        if self._task:
            self._task.cancel()
        
        self._task = self.hass.async_create_task(self._async_call())

    async def _async_call(self):
        """Call the function after the delay."""
        await asyncio.sleep(self.seconds)
        await self.function()