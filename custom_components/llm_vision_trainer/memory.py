"""Safe manager for the three parallel LLM Vision 1.7.1 memory arrays."""
from __future__ import annotations

import asyncio
import base64
import binascii
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Any

from .adapter import LlmVisionAdapter
from .const import ALLOWED_IMAGE_SUFFIXES, MEMORY_BACKUP_DIR, MEMORY_QUARANTINE_DIR

_SAFE_NAME = re.compile(r"^[^/\\\x00]+$")


class MemoryError(RuntimeError):
    pass


class MemoryConflict(MemoryError):
    pass


class MemoryManager:
    def __init__(self, hass, adapter: LlmVisionAdapter) -> None:
        self.hass = hass
        self.adapter = adapter
        self._lock = asyncio.Lock()
        self._storage = Path(hass.config.path(".storage"))
        self._backup_dir = self._storage / MEMORY_BACKUP_DIR
        self._quarantine_dir = self._storage / MEMORY_QUARANTINE_DIR

    @staticmethod
    def _id(index: int, path: str) -> str:
        return hashlib.sha256(f"{index}\x00{path}".encode()).hexdigest()[:24]

    @staticmethod
    def _validate(snapshot: dict[str, Any]) -> int:
        values = [snapshot[k] for k in ("memory_paths", "memory_strings", "images")]
        if not all(isinstance(v, list) for v in values):
            raise MemoryConflict("I campi memoria non sono liste")
        paths, strings, images = values
        if len(paths) != len(strings) or len(images) not in (0, len(paths)):
            raise MemoryConflict("Array memoria incoerenti: paths e strings devono coincidere; images può essere vuoto o completo")
        return len(paths)

    def _read(self):
        entry, snapshot = self.adapter.memory_config()
        return entry, snapshot

    async def list(self) -> dict[str, Any]:
        entry, snap = self._read()
        paths, strings, images = (snap[k] for k in ("memory_paths", "memory_strings", "images"))
        diagnostics: list[dict[str, Any]] = []
        if len(paths) != len(strings) or len(images) not in (0, len(paths)):
            diagnostics.append({"code": "cardinality_mismatch", "severity": "error", "counts": {"paths": len(paths), "strings": len(strings), "images": len(images)}})
        elif paths and not images:
            diagnostics.append({"code": "deferred_image_cache", "severity": "info", "counts": {"paths": len(paths), "strings": len(strings), "images": 0}})
        duplicate_paths = {p for p in paths if paths.count(p) > 1}
        items = []
        for index in range(max(len(paths), len(strings), len(images), 0)):
            path = str(paths[index]) if index < len(paths) else ""
            description = str(strings[index]) if index < len(strings) else ""
            encoded = str(images[index]) if index < len(images) else ""
            exists, size, modified = await self.hass.async_add_executor_job(self._stat, path)
            item_id = self._id(index, path)
            issues = []
            if path and not exists: issues.append("missing_file")
            if path in duplicate_paths: issues.append("duplicate_path")
            if images and not encoded: issues.append("missing_cached_image")
            items.append({"id": item_id, "index": index, "path": path, "filename": Path(path).name if path else "", "description": description,
                          "exists": exists, "size": size, "modified": modified, "issues": issues,
                          "thumbnail_url": f"/api/llm_vision_trainer/memory/{item_id}/image" if encoded or exists else None})
        return {"entry_id": entry.entry_id, "items": items, "diagnostics": diagnostics, "counts": {"paths": len(paths), "strings": len(strings), "images": len(images)}}

    @staticmethod
    def _stat(path: str) -> tuple[bool, int | None, str | None]:
        try:
            stat = Path(path).stat()
            return True, stat.st_size, datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        except (OSError, ValueError):
            return False, None, None

    def image(self, item_id: str) -> tuple[bytes, str]:
        _, snap = self._read()
        for index, path in enumerate(snap["memory_paths"]):
            if self._id(index, str(path)) != item_id:
                continue
            if index < len(snap["images"]) and snap["images"][index]:
                raw = str(snap["images"][index])
                if raw.startswith("data:"):
                    header, raw = raw.split(",", 1)
                    content_type = header[5:].split(";", 1)[0] or "image/jpeg"
                else: content_type = "image/jpeg"
                try: return base64.b64decode(raw, validate=True), content_type
                except (binascii.Error, ValueError) as err: raise MemoryError("Immagine Base64 non valida") from err
            image_path = Path(str(path))
            if not image_path.is_file() or image_path.suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
                raise MemoryError("File immagine non disponibile")
            content_type = {".png":"image/png", ".webp":"image/webp"}.get(image_path.suffix.lower(), "image/jpeg")
            return image_path.read_bytes(), content_type
        raise KeyError(item_id)

    async def update_description(self, item_id: str, description: str) -> dict[str, Any]:
        async with self._lock:
            entry, snap, index = self._locate(item_id)
            original = deepcopy(snap)
            snap["memory_strings"][index] = str(description).strip()[:4096]
            await self._commit(entry, snap, "description", original)
            return {"status": "ok", "id": self._id(index, snap["memory_paths"][index])}

    async def reorder(self, item_id: str, new_index: int) -> dict[str, Any]:
        async with self._lock:
            entry, snap, index = self._locate(item_id)
            original = deepcopy(snap)
            count = self._validate(snap)
            if not 0 <= new_index < count: raise MemoryError("Posizione non valida")
            for key in ("memory_paths", "memory_strings"):
                value = snap[key].pop(index); snap[key].insert(new_index, value)
            if snap["images"]:
                value = snap["images"].pop(index); snap["images"].insert(new_index, value)
            await self._commit(entry, snap, "reorder", original)
            return {"status": "ok", "id": self._id(new_index, snap["memory_paths"][new_index])}

    async def rename(self, item_id: str, filename: str) -> dict[str, Any]:
        if not _SAFE_NAME.fullmatch(filename or "") or filename in {".", ".."}: raise MemoryError("Nome file non valido")
        if Path(filename).suffix.lower() not in ALLOWED_IMAGE_SUFFIXES: raise MemoryError("Estensione immagine non supportata")
        async with self._lock:
            entry, snap, index = self._locate(item_id)
            original = deepcopy(snap)
            old = Path(snap["memory_paths"][index]); new = old.with_name(filename)
            if new == old: return {"status": "ok", "id": item_id}
            await self.hass.async_add_executor_job(self._rename_file, old, new)
            snap["memory_paths"][index] = str(new)
            try: await self._commit(entry, snap, "rename", original)
            except Exception:
                await self.hass.async_add_executor_job(os.replace, new, old)
                raise
            return {"status": "ok", "id": self._id(index, str(new)), "path": str(new)}

    async def delete(self, item_id: str, confirm_external: bool = False) -> dict[str, Any]:
        async with self._lock:
            entry, snap, index = self._locate(item_id)
            original = deepcopy(snap)
            source = Path(snap["memory_paths"][index])
            external = not self._is_owned(source)
            if external and not confirm_external: raise MemoryError("Conferma esplicita richiesta per rimuovere un file esterno")
            quarantine = None
            if source.exists():
                quarantine = self._quarantine_dir / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}-{source.name}"
                await self.hass.async_add_executor_job(self._move_to_quarantine, source, quarantine)
            for key in ("memory_paths", "memory_strings"): snap[key].pop(index)
            if snap["images"]: snap["images"].pop(index)
            try: await self._commit(entry, snap, "delete", original)
            except Exception:
                if quarantine and quarantine.exists(): await self.hass.async_add_executor_job(self._restore_quarantine, quarantine, source)
                raise
            return {"status": "ok", "quarantined": str(quarantine) if quarantine else None, "external": external}

    def _locate(self, item_id: str):
        entry, snap = self._read(); self._validate(snap)
        for index, path in enumerate(snap["memory_paths"]):
            if self._id(index, str(path)) == item_id: return entry, deepcopy(snap), index
        raise KeyError(item_id)

    async def _commit(self, entry, snap: dict[str, Any], operation: str, original: dict[str, Any]) -> None:
        self._validate(snap)
        current_entry, current = self._read()
        if current_entry.entry_id != entry.entry_id: raise MemoryConflict("La config entry Settings è cambiata")
        self._validate(current)
        if any(current[k] != original[k] for k in ("memory_paths", "memory_strings", "images")):
            raise MemoryConflict("La memoria LLM Vision è cambiata durante l'operazione; nessun dato è stato sovrascritto")
        await self.hass.async_add_executor_job(self._write_backup, entry.entry_id, operation, current)
        values = {k: snap[k] for k in ("memory_paths", "memory_strings", "images")}
        if snap["location"] == "options":
            merged = dict(entry.options); merged.update(values)
            self.hass.config_entries.async_update_entry(entry, options=merged)
        else:
            merged = dict(entry.data); merged.update(values)
            self.hass.config_entries.async_update_entry(entry, data=merged)

    def _write_backup(self, entry_id: str, operation: str, snap: dict[str, Any]) -> None:
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        target = self._backup_dir / f"{stamp}-{operation}.json"
        temp = target.with_suffix(".tmp")
        payload = {"created_at": datetime.now(timezone.utc).isoformat(), "entry_id": entry_id, "operation": operation,
                   "memory_paths": snap["memory_paths"], "memory_strings": snap["memory_strings"], "images": snap["images"]}
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"); os.replace(temp, target)

    def _is_owned(self, path: Path) -> bool:
        try: path.resolve().relative_to(self._storage.resolve()); return True
        except (ValueError, OSError): return False

    @staticmethod
    def _rename_file(old: Path, new: Path) -> None:
        if not old.is_file(): raise MemoryError("File sorgente mancante")
        if new.exists(): raise MemoryConflict("Esiste già un file con questo nome")
        os.replace(old, new)

    def _move_to_quarantine(self, source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists(): raise MemoryConflict("Destinazione quarantena già esistente")
        shutil.move(str(source), str(target))

    @staticmethod
    def _restore_quarantine(source: Path, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(source), str(target))
