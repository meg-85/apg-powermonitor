"""Calendar showing the forecast peak periods of the Austrian grid."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .api import PeakPeriod
from .coordinator import ApgConfigEntry
from .entity import ApgEntity

EVENT_SUMMARY = "Spitzenzeit Stromnetz"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ApgConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([ApgPeakCalendar(entry.runtime_data)])


def _to_event(period: PeakPeriod) -> CalendarEvent:
    return CalendarEvent(
        start=dt_util.as_local(period.start),
        end=dt_util.as_local(period.end),
        summary=EVENT_SUMMARY,
    )


class ApgPeakCalendar(ApgEntity, CalendarEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "peak_calendar")

    @property
    def event(self) -> CalendarEvent | None:
        period = self.coordinator.data.current_or_next_period(dt_util.utcnow())
        return _to_event(period) if period else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            _to_event(p)
            for p in self.coordinator.data.periods
            if p.end > start_date and p.start < end_date
        ]
