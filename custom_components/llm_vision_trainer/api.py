from __future__ import annotations
from aiohttp import web
from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from .const import DEFAULT_LABELS, DOMAIN
from .memory import MemoryConflict, MemoryError


def runtime(request): return request.app["hass"].data[DOMAIN]["runtime"]
def error(view, message, status=400): return view.json({"error": message}, status_code=status)

class CandidatesView(HomeAssistantView):
    url = "/api/llm_vision_trainer/candidates"; name = "api:llm_vision_trainer:candidates"; requires_auth = True
    async def get(self, request):
        rt = runtime(request)
        try: await rt.async_refresh()
        except Exception as err: rt.last_error = str(err)
        data = await rt.store.snapshot()
        items = [x for x in data["candidates"].values() if x.get("image_id") and x["event_id"] not in data["classifications"]]
        items.sort(key=lambda x: x.get("occurred_at") or x.get("discovered_at") or "", reverse=True)
        return self.json({"items": items, "labels": DEFAULT_LABELS, "error": rt.last_error})
class ClassifiedView(HomeAssistantView):
    url = "/api/llm_vision_trainer/classified"; name = "api:llm_vision_trainer:classified"; requires_auth = True
    async def get(self, request):
        data = await runtime(request).store.snapshot(); items = list(data["classifications"].values())
        items.sort(key=lambda x: x.get("updated_at", ""), reverse=True); return self.json({"items": items, "labels": DEFAULT_LABELS})
class ClassificationView(HomeAssistantView):
    url = "/api/llm_vision_trainer/classifications/{event_id}"; name = "api:llm_vision_trainer:classification"; requires_auth = True
    async def post(self, request, event_id):
        try: payload = await request.json()
        except Exception: return error(self, "Corpo JSON non valido")
        label = str(payload.get("label", "")).strip().lower()
        if label not in DEFAULT_LABELS: return error(self, "Etichetta non valida")
        saved = await runtime(request).store.classify(str(event_id), label)
        return self.json({"classification": saved}) if saved else error(self, "Evento candidato non trovato", 404)
    async def delete(self, request, event_id):
        requeue = request.query.get("requeue", "1") not in {"0", "false"}
        ok = await runtime(request).store.remove_classification(str(event_id), requeue)
        return self.json({"status": "ok", "requeued": requeue}) if ok else error(self, "Classificazione non trovata", 404)
class ImageView(HomeAssistantView):
    url = "/api/llm_vision_trainer/images/{image_id}"; name = "api:llm_vision_trainer:image"; requires_auth = True
    async def get(self, request, image_id): return await runtime(request).images.response(image_id)

class MemoryView(HomeAssistantView):
    url = "/api/llm_vision_trainer/memory"; name = "api:llm_vision_trainer:memory"; requires_auth = True
    async def get(self, request):
        try: return self.json(await runtime(request).memory.list())
        except Exception as err: return error(self, str(err), 409)

class MemoryItemView(HomeAssistantView):
    url = "/api/llm_vision_trainer/memory/{item_id}"; name = "api:llm_vision_trainer:memory_item"; requires_auth = True
    async def post(self, request, item_id):
        try: payload = await request.json()
        except Exception: return error(self, "Corpo JSON non valido")
        try:
            action = payload.get("action")
            manager = runtime(request).memory
            if action == "description": result = await manager.update_description(item_id, payload.get("description", ""))
            elif action == "rename": result = await manager.rename(item_id, str(payload.get("filename", "")))
            elif action == "reorder": result = await manager.reorder(item_id, int(payload.get("index", -1)))
            elif action == "delete": result = await manager.delete(item_id, payload.get("confirm_external") is True)
            else: return error(self, "Azione non valida")
            return self.json(result)
        except KeyError: return error(self, "Elemento memoria non trovato", 404)
        except (MemoryError, MemoryConflict, ValueError) as err: return error(self, str(err), 409)
    async def delete(self, request, item_id):
        try:
            payload = await request.json() if request.can_read_body else {}
            result = await runtime(request).memory.delete(item_id, payload.get("confirm_external") is True)
            return self.json(result)
        except KeyError: return error(self, "Elemento memoria non trovato", 404)
        except (MemoryError, MemoryConflict) as err: return error(self, str(err), 409)

class MemoryImageView(HomeAssistantView):
    url = "/api/llm_vision_trainer/memory/{item_id}/image"; name = "api:llm_vision_trainer:memory_image"; requires_auth = True
    async def get(self, request, item_id):
        try:
            body, content_type = runtime(request).memory.image(item_id)
            return web.Response(body=body, content_type=content_type, headers={"Cache-Control": "private, max-age=60"})
        except KeyError: raise web.HTTPNotFound()
        except MemoryError as err: return error(self, str(err), 422)

def async_register_views(hass: HomeAssistant) -> None:
    if hass.data.get(f"{DOMAIN}_views_registered"): return
    for view in (CandidatesView, ClassifiedView, ClassificationView, ImageView, MemoryView, MemoryItemView, MemoryImageView): hass.http.register_view(view())
    hass.data[f"{DOMAIN}_views_registered"] = True
