"""Sensors for the APG peak hour forecast."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.util import dt as dt_util

from .api import PeakHourData
from .coordinator import ApgConfigEntry, ApgCoordinator
from .entity import ApgEntity


def _peak_hours_on_local_day(data: PeakHourData, now: datetime, offset: int) -> int | None:
    """Count peak hours on today (+offset days) in local time, DST-safe."""
    day = dt_util.as_local(now).date() + timedelta(days=offset)
    start = dt_util.as_utc(dt_util.start_of_local_day(day))
    end = dt_util.as_utc(dt_util.start_of_local_day(day + timedelta(days=1)))
    return data.peak_hours_between(start, end)


def _period_start(data: PeakHourData, now: datetime) -> datetime | None:
    period = data.current_or_next_period(now)
    return period.start if period else None


def _period_end(data: PeakHourData, now: datetime) -> datetime | None:
    period = data.current_or_next_period(now)
    return period.end if period else None


@dataclass(frozen=True, kw_only=True)
class ApgSensorDescription(SensorEntityDescription):
    value_fn: Callable[[PeakHourData, datetime], StateType | datetime]


SENSORS: tuple[ApgSensorDescription, ...] = (
    ApgSensorDescription(
        key="period_start",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_period_start,
    ),
    ApgSensorDescription(
        key="period_end",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=_period_end,
    ),
    ApgSensorDescription(
        key="peak_hours_today",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda data, now: _peak_hours_on_local_day(data, now, 0),
    ),
    ApgSensorDescription(
        key="peak_hours_tomorrow",
        native_unit_of_measurement=UnitOfTime.HOURS,
        value_fn=lambda data, now: _peak_hours_on_local_day(data, now, 1),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ApgConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(ApgSensor(coordinator, description) for description in SENSORS)


class ApgSensor(ApgEntity, SensorEntity):
    entity_description: ApgSensorDescription

    def __init__(self, coordinator: ApgCoordinator, description: ApgSensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType | datetime:
        return self.entity_description.value_fn(self.coordinator.data, dt_util.utcnow())
