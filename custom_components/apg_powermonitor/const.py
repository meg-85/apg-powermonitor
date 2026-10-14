"""Constants for the APG Powermonitor integration."""

from datetime import timedelta
import logging

DOMAIN = "apg_powermonitor"
LOGGER = logging.getLogger(__package__)

# The forecast is published once a day (around 09:30); hourly polling is plenty.
UPDATE_INTERVAL = timedelta(hours=1)

# Notice requested by APG for users of the public API.
ATTRIBUTION = (
    "Mehr zum Thema sichere Stromversorgung & Zahlen, Daten, Fakten zur Welt "
    "des Stroms bzw. zur Energiewende finden Sie unter https://www.apg.at/powermonitor/"
)
CONFIGURATION_URL = "https://www.apg.at/powermonitor/"
