"""Serve and register the bundled Lovelace card."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import CONF_RESOURCE_TYPE_WS
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant

from .const import CARD_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)
_FRONTEND_DIR = Path(__file__).parent / "frontend"


def _lovelace_data(hass: HomeAssistant) -> Any:
    data = hass.data.get("lovelace")
    if data is None:
        return None
    return data.get("resources") if isinstance(data, dict) else getattr(data, "resources", None)


def _resource_mode(hass: HomeAssistant) -> str | None:
    data = hass.data.get("lovelace")
    if data is None:
        return None
    return data.get("resource_mode") if isinstance(data, dict) else getattr(data, "resource_mode", None)


async def async_register_frontend(hass: HomeAssistant) -> None:
    """Expose the bundled card and add it to storage-mode resources once."""
    marker = f"{DOMAIN}_frontend_registered"
    if hass.data.get(marker):
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(_FRONTEND_DIR / "llm-vision-trainer-card.js"), True)]
    )
    hass.data[marker] = True

    resources = _lovelace_data(hass)
    if resources is None:
        _LOGGER.warning("Lovelace is unavailable; add %s manually as a JavaScript module", CARD_URL)
        return
    if _resource_mode(hass) == "yaml":
        _LOGGER.warning("Lovelace resources use YAML mode; add %s manually as type module", CARD_URL)
        return

    # Older Home Assistant releases lazily loaded the collection. Loading first
    # prevents replacing an existing resource store with an incomplete snapshot.
    if hasattr(resources, "async_load") and not getattr(resources, "loaded", True):
        await resources.async_load()
    items = resources.async_items()
    if any(str(item.get(CONF_URL, "")).split("?", 1)[0] == CARD_URL for item in items):
        return
    await resources.async_create_item({CONF_URL: CARD_URL, CONF_RESOURCE_TYPE_WS: "module"})
