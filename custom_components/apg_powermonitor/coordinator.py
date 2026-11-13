"""Data update coordinator for APG Powermonitor."""

from __future__ import annotations

from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import ApgApiError, ApgClient, PeakHourData
from .const import DOMAIN, LOGGER, MAX_DATA_AGE, RETRY_INTERVAL, UPDATE_INTERVAL

type ApgConfigEntry = ConfigEntry[ApgCoordinator]


class ApgCoordinator(DataUpdateCoordinator[PeakHourData]):
    """Fetches the peak hour forecast once per interval for all entities.

    A failed fetch does not make the entities unavailable as long as the last
    good forecast still covers the current hour and is younger than
    MAX_DATA_AGE. Until the next success it is retried every RETRY_INTERVAL.
    """

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
        self.last_success: datetime | None = None
        self._failures = 0

    async def _async_update_data(self) -> PeakHourData:
        try:
            data = await self.client.async_get_peak_hours()
        except ApgApiError as err:
            return self._handle_failure(err)

        if self._failures:
            LOGGER.info("APG API reachable again after %s failed attempt(s)", self._failures)
        self._failures = 0
        self.last_success = dt_util.utcnow()
        self.update_interval = UPDATE_INTERVAL
        return data

    def _handle_failure(self, err: ApgApiError) -> PeakHourData:
        """Keep the last good forecast if it is still usable, else fail."""
        self._failures += 1
        self.update_interval = RETRY_INTERVAL
        now = dt_util.utcnow()
        usable = (
            self.data is not None
            and self.last_success is not None
            and now - self.last_success < MAX_DATA_AGE
            and self.data.has_data_for(now)
        )
        if not usable:
            raise UpdateFailed(str(err)) from err

        log = LOGGER.warning if self._failures == 1 else LOGGER.debug
        log(
            "%s - keeping forecast from %s, retrying in %s",
            err,
            dt_util.as_local(self.last_success).strftime("%d.%m. %H:%M"),
            RETRY_INTERVAL,
        )
        return self.data
