"""Data update coordinator for APG Powermonitor."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ApgApiError, ApgClient, PeakHourData
from .const import DOMAIN, LOGGER, UPDATE_INTERVAL

type ApgConfigEntry = ConfigEntry[ApgCoordinator]


class ApgCoordinator(DataUpdateCoordinator[PeakHourData]):
    """Fetches the peak hour forecast once per interval for all entities."""

    config_entry: ApgConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: ApgConfigEntry, client: ApgClient
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> PeakHourData:
        try:
            return await self.client.async_get_peak_hours()
        except ApgApiError as err:
            raise UpdateFailed(str(err)) from err
