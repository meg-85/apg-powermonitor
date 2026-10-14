"""The APG Powermonitor integration."""

from __future__ import annotations

from datetime import datetime

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_utc_time_change

from .api import ApgClient
from .coordinator import ApgConfigEntry, ApgCoordinator

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ApgConfigEntry) -> bool:
    """Set up APG Powermonitor from a config entry."""
    coordinator = ApgCoordinator(hass, entry, ApgClient(async_get_clientsession(hass)))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    # Peak status changes on the full hour, independent of the API polling.
    # Re-evaluate all entities right after each hour boundary.
    @callback
    def _hour_changed(_now: datetime) -> None:
        coordinator.async_update_listeners()

    entry.async_on_unload(
        async_track_utc_time_change(hass, _hour_changed, minute=0, second=1)
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ApgConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
