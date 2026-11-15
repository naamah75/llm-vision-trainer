from __future__ import annotations
import logging
from homeassistant.helpers.storage import Store
from .store import TrainerStore
_LOGGER = logging.getLogger(__name__)
async def async_migrate_ring_training(hass, store: TrainerStore) -> int:
    try: raw = await Store(hass, 1, "ring_training.labels").async_load()
    except Exception as err:
        _LOGGER.debug("Legacy ring_training storage unavailable: %s", err); return 0
    labels = (raw or {}).get("labels")
    return await store.import_legacy(labels) if isinstance(labels, dict) else 0
