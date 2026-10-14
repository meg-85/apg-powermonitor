"""API client and data model for the APG Powermonitor peak hour status.

This module has no Home Assistant imports so it can be tested on its own.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import aiohttp

PEAK_HOUR_URL = "https://awareness.cloud.apg.at/api/v1/PeakHourStatus"
HOUR = timedelta(hours=1)
REQUEST_TIMEOUT = 20


class ApgApiError(Exception):
    """The API could not be reached or returned unusable data."""


@dataclass(frozen=True)
class PeakPeriod:
    """A block of consecutive peak hours. `end` is exclusive."""

    start: datetime
    end: datetime


@dataclass(frozen=True)
class PeakHourData:
    """Parsed response of the PeakHourStatus endpoint.

    The API only lists hours whose status differs from `default_status`;
    every hour not listed has the default status (no peak).
    """

    first_utc: datetime
    last_utc: datetime
    default_status: str
    statuses: dict[datetime, str]
    periods: tuple[PeakPeriod, ...]

    def has_data_for(self, when: datetime) -> bool:
        """Return True if the forecast covers this point in time."""
        return self.first_utc <= when < self.last_utc + HOUR

    def status_at(self, when: datetime) -> str:
        """Return the raw status of the hour containing `when`."""
        return self.statuses.get(_floor_hour(when), self.default_status)

    def is_peak(self, when: datetime) -> bool | None:
        """Return whether `when` is in a peak hour, or None if not covered."""
        if not self.has_data_for(when):
            return None
        return self.status_at(when) != self.default_status

    def current_or_next_period(self, when: datetime) -> PeakPeriod | None:
        """Return the period running at `when`, else the next one."""
        return next((p for p in self.periods if p.end > when), None)

    def next_period(self, when: datetime) -> PeakPeriod | None:
        """Return the first period that starts after `when`."""
        return next((p for p in self.periods if p.start > when), None)

    def peak_hours_between(self, start: datetime, end: datetime) -> int | None:
        """Count peak hours in [start, end), or None if not fully covered."""
        if not (self.has_data_for(start) and self.has_data_for(end - HOUR)):
            return None
        return sum(
            1
            for hour, status in self.statuses.items()
            if start <= hour < end and status != self.default_status
        )


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _floor_hour(when: datetime) -> datetime:
    return when.replace(minute=0, second=0, microsecond=0)


def parse_peak_hour_status(payload: dict[str, Any]) -> PeakHourData:
    """Turn the raw JSON payload into PeakHourData."""
    try:
        default_status = str(payload["DefaultStatus"])
        first_utc = _parse_utc(payload["FirstUtc"])
        last_utc = _parse_utc(payload["LastUtc"])
        statuses = {
            _parse_utc(item["utc"]): str(item["s"])
            for item in payload["StatusInfos"]
        }
    except (KeyError, TypeError, ValueError) as err:
        raise ApgApiError(f"Unexpected response format: {err}") from err

    periods: list[PeakPeriod] = []
    for hour in sorted(h for h, s in statuses.items() if s != default_status):
        if periods and periods[-1].end == hour:
            periods[-1] = PeakPeriod(periods[-1].start, hour + HOUR)
        else:
            periods.append(PeakPeriod(hour, hour + HOUR))

    return PeakHourData(
        first_utc=first_utc,
        last_utc=last_utc,
        default_status=default_status,
        statuses=statuses,
        periods=tuple(periods),
    )


class ApgClient:
    """Minimal async client for the APG Powermonitor API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def async_get_peak_hours(self) -> PeakHourData:
        """Fetch and parse the peak hour forecast."""
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.get(
                    PEAK_HOUR_URL, headers={"Accept": "application/json"}
                )
                response.raise_for_status()
                payload = await response.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ApgApiError(f"Error talking to APG API: {err}") from err
        return parse_peak_hour_status(payload)
