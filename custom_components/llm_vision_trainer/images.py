"""Copy and serve only images owned by Trainer."""
from __future__ import annotations
import hashlib, mimetypes, shutil
from pathlib import Path
from aiohttp import web
from homeassistant.core import HomeAssistant
from .const import ALLOWED_IMAGE_SUFFIXES, IMAGE_DIR

class ImageManager:
    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass; self.root = Path(hass.config.path(".storage", IMAGE_DIR))

    def _source(self, value: str) -> Path | None:
        raw = Path(value)
        filename = raw.name
        candidates = [raw, Path(self.hass.config.path("media/llmvision/snapshots")) / filename, Path("/media/llmvision/snapshots") / filename]
        allowed_roots = [Path(self.hass.config.path()).resolve(), Path("/media").resolve()]
        for item in candidates:
            try: resolved = item.resolve()
            except OSError: continue
            if resolved.suffix.lower() in ALLOWED_IMAGE_SUFFIXES and any(resolved.is_relative_to(root) for root in allowed_roots) and resolved.is_file(): return resolved
        return None

    async def copy(self, event_id: str, source: str) -> str:
        src = await self.hass.async_add_executor_job(self._source, source)
        if src is None: return ""
        image_id = hashlib.sha256((event_id + "\0" + str(src)).encode()).hexdigest()[:32] + src.suffix.lower()
        target = self.root / image_id
        def do_copy():
            self.root.mkdir(parents=True, exist_ok=True)
            if not target.exists(): shutil.copy2(src, target)
        await self.hass.async_add_executor_job(do_copy); return image_id

    async def response(self, image_id: str) -> web.FileResponse:
        if Path(image_id).name != image_id or Path(image_id).suffix.lower() not in ALLOWED_IMAGE_SUFFIXES: raise web.HTTPNotFound()
        path = (self.root / image_id).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file(): raise web.HTTPNotFound()
        response = web.FileResponse(path, headers={"Cache-Control": "private, max-age=3600", "X-Content-Type-Options": "nosniff"})
        response.content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return response

    def path(self, image_id: str) -> Path:
        """Return a validated Trainer-owned image path."""
        if Path(image_id).name != image_id or Path(image_id).suffix.lower() not in ALLOWED_IMAGE_SUFFIXES:
            raise FileNotFoundError(image_id)
        path = (self.root / image_id).resolve()
        if not path.is_relative_to(self.root.resolve()) or not path.is_file():
            raise FileNotFoundError(image_id)
        return path
