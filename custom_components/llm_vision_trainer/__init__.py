"""Unofficial companion integration for reviewing LLM Vision events."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .adapter import AdapterUnavailable, LlmVisionAdapter
from .api import async_register_views
from .const import DOMAIN
from .frontend import async_register_frontend
from .images import ImageManager
from .memory import MemoryManager
from .migration import async_migrate_ring_training
from .store import TrainerStore


@dataclass
class TrainerRuntime:
    store: TrainerStore
    images: ImageManager
    adapter: LlmVisionAdapter
    memory: MemoryManager
    last_error: str = ""

    async def async_refresh(self) -> None:
        events = await self.adapter.events()
        candidates = []
        for event in events:
            if not event.source_image:
                continue
            event.image_id = await self.images.copy(event.event_id, event.source_image)
            if event.image_id:
                candidates.append(event.as_dict())
        await self.store.upsert_candidates(candidates)
        self.last_error = ""


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    async_register_views(hass)
    await async_register_frontend(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = TrainerStore(hass)
    adapter = LlmVisionAdapter(hass)
    runtime = TrainerRuntime(store, ImageManager(hass), adapter, MemoryManager(hass, adapter))
    hass.data.setdefault(DOMAIN, {})["runtime"] = runtime
    await async_migrate_ring_training(hass, store)
    try:
        await runtime.async_refresh()
    except AdapterUnavailable as err:
        runtime.last_error = str(err)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.get(DOMAIN, {}).pop("runtime", None)
    return True
