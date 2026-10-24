"""Calendar showing the forecast peak periods of the Austrian grid."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import PeakPeriod, split_at_local_midnight
from .coordinator import ApgConfigEntry
from .entity import ApgEntity

EVENT_SUMMARY = "Spitzenzeit"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ApgConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([ApgPeakCalendar(entry.runtime_data)])


def _fmt(when: datetime) -> str:
    return dt_util.as_local(when).strftime("%d.%m. %H:%M")


def _to_events(period: PeakPeriod) -> list[CalendarEvent]:
    """One event per local day; the description names the full peak block."""
    description = f"Spitzenzeit {_fmt(period.start)} – {_fmt(period.end)}"
    return [
        CalendarEvent(start=start, end=end, summary=EVENT_SUMMARY, description=description)
        for start, end in split_at_local_midnight(
            period.start, period.end, dt_util.get_default_time_zone()
        )
    ]


class ApgPeakCalendar(ApgEntity, CalendarEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "peak_calendar")

    def _events(self) -> list[CalendarEvent]:
        return [e for p in self.coordinator.data.periods for e in _to_events(p)]

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.now()
        return next((e for e in self._events() if e.end > now), None)

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [e for e in self._events() if e.end > start_date and e.start < end_date]
