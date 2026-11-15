"""Version-tolerant boundary around optional LLM Vision interfaces."""
from __future__ import annotations
import logging
from typing import Any
from homeassistant.core import HomeAssistant
from .models import CandidateEvent
_LOGGER = logging.getLogger(__name__)

class AdapterUnavailable(RuntimeError): pass
class LlmVisionAdapter:
    def __init__(self, hass: HomeAssistant) -> None: self.hass = hass
    def settings_entry(self):
        entries = self.hass.config_entries.async_entries("llmvision")
        entry = next((e for e in entries if e.data.get("provider") == "Settings"), None)
        if entry is None:
            entry = next((e for e in entries if str(getattr(e, "title", "")).strip().lower() == "settings"), None)
        if entry is None: raise AdapterUnavailable("Config entry Settings di LLM Vision non trovata")
        return entry

    def memory_config(self) -> tuple[Any, dict[str, Any]]:
        """Return the Settings entry and a detached, normalized memory snapshot."""
        entry = self.settings_entry()
        options = getattr(entry, "options", {}) or {}
        source = options if all(k in options for k in ("memory_paths", "memory_strings", "images")) else entry.data
        return entry, {
            "memory_paths": list(source.get("memory_paths") or []),
            "memory_strings": list(source.get("memory_strings") or []),
            "images": list(source.get("images") or []),
            "location": "options" if source is entry.options else "data",
        }
    async def events(self, limit: int = 100) -> list[CandidateEvent]:
        settings = self.settings_entry()
        try:
            from custom_components.llmvision.timeline import Timeline  # optional, isolated compatibility bridge
        except (ImportError, ModuleNotFoundError) as err: raise AdapterUnavailable("La versione installata di LLM Vision non espone una timeline compatibile") from err
        try:
            timeline = Timeline(self.hass, settings)
            getter = getattr(timeline, "get_events_json", None)
            if getter is None: raise AdapterUnavailable("API timeline LLM Vision non disponibile")
            raw: Any = await getter(limit=limit, include_no_activity=True)
        except AdapterUnavailable: raise
        except Exception as err:
            _LOGGER.warning("LLM Vision adapter unavailable: %s", err)
            raise AdapterUnavailable("Impossibile leggere gli eventi da LLM Vision") from err
        if isinstance(raw, dict): raw = raw.get("events", [])
        return [event for item in (raw or []) if isinstance(item, dict) and (event := CandidateEvent.from_mapping(item)).event_id]
