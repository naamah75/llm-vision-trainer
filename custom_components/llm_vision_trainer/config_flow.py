from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import DEFAULT_MAX_EXAMPLES, DOMAIN

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        if user_input is not None:
            return self.async_create_entry(title="LLM Vision Trainer", data=user_input)
        schema = vol.Schema({vol.Optional("source_integration", default="llmvision"): str})
        return self.async_show_form(step_id="user", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlow()

class OptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        schema = vol.Schema({vol.Optional("max_examples", default=self.config_entry.options.get("max_examples", DEFAULT_MAX_EXAMPLES)): vol.All(vol.Coerce(int), vol.Range(min=1, max=10))})
        return self.async_show_form(step_id="init", data_schema=schema)
