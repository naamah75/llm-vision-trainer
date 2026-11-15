from __future__ import annotations
import asyncio
from copy import deepcopy
from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from .const import STORE_KEY, STORE_VERSION
from .models import Classification, utcnow

EMPTY = {"schema": STORE_VERSION, "candidates": {}, "classifications": {}, "migration": {}}

class TrainerStore:
    def __init__(self, hass: HomeAssistant) -> None:
        self._store = Store(hass, STORE_VERSION, STORE_KEY)
        self._lock = asyncio.Lock()
        self._data: dict[str, Any] | None = None

    async def _load_locked(self) -> dict[str, Any]:
        if self._data is None:
            raw = await self._store.async_load() or {}
            self._data = deepcopy(EMPTY)
            for key in EMPTY:
                if isinstance(raw.get(key), dict): self._data[key].update(raw[key])
        return self._data

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock: return deepcopy(await self._load_locked())

    async def upsert_candidates(self, items: list[dict[str, Any]]) -> None:
        async with self._lock:
            data = await self._load_locked()
            for item in items:
                event_id = str(item.get("event_id", ""))
                if event_id and event_id not in data["classifications"]: data["candidates"][event_id] = item
            await self._store.async_save(data)

    async def classify(self, event_id: str, label: str) -> dict[str, Any] | None:
        async with self._lock:
            data = await self._load_locked(); candidate = data["candidates"].pop(event_id, None)
            old = data["classifications"].get(event_id)
            if candidate is None and old: candidate = old.get("candidate", {})
            if candidate is None: return None
            record = Classification(event_id, label, updated_at=utcnow(), candidate=candidate,
                                    classified_at=(old or {}).get("classified_at", utcnow()), migrated=bool((old or {}).get("migrated"))).as_dict()
            data["classifications"][event_id] = record; await self._store.async_save(data); return deepcopy(record)

    async def remove_classification(self, event_id: str, requeue: bool = True) -> bool:
        async with self._lock:
            data = await self._load_locked(); record = data["classifications"].pop(event_id, None)
            if not record: return False
            candidate = record.get("candidate") or {}
            if requeue and candidate.get("event_id") and candidate.get("image_id"): data["candidates"][event_id] = candidate
            await self._store.async_save(data); return True

    async def import_legacy(self, labels: dict[str, Any]) -> int:
        async with self._lock:
            data = await self._load_locked()
            if data["migration"].get("ring_training_v1"): return 0
            count = 0
            for event_id, label in labels.items():
                event_id, label = str(event_id), str(label)
                if event_id and label and event_id not in data["classifications"]:
                    data["classifications"][event_id] = Classification(event_id, label, candidate={"event_id": event_id, "source": "ring_training"}, migrated=True).as_dict(); count += 1
            data["migration"]["ring_training_v1"] = {"completed_at": utcnow(), "imported": count}
            await self._store.async_save(data); return count
