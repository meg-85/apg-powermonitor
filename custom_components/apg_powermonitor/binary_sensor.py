"""Binary sensor: is the Austrian grid currently in a peak hour?"""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import ApgConfigEntry
from .entity import ApgEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ApgConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([ApgPeakHourBinarySensor(entry.runtime_data)])


class ApgPeakHourBinarySensor(ApgEntity, BinarySensorEntity):
    """On while the current hour is a peak hour (residual load > 3000 MW)."""

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "peak_hour")

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.is_peak(dt_util.utcnow())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        period = self.coordinator.data.current_or_next_period(dt_util.utcnow())
        return {
            "period_start": dt_util.as_local(period.start).isoformat() if period else None,
            "period_end": dt_util.as_local(period.end).isoformat() if period else None,
        }
