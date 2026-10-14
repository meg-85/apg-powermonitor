"""Config flow for APG Powermonitor."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApgApiError, ApgClient
from .const import DOMAIN


class ApgConfigFlow(ConfigFlow, domain=DOMAIN):
    """Nothing to configure: confirm, test the API, create the entry."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            client = ApgClient(async_get_clientsession(self.hass))
            try:
                await client.async_get_peak_hours()
            except ApgApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(title="APG Powermonitor", data={})

        return self.async_show_form(step_id="user", errors=errors)
