"""Stable, JSON-serialisable data model owned by Trainer."""
from __future__ import annotations
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value: Any, limit: int = 4096) -> str:
    return str(value or "").strip()[:limit]

@dataclass(slots=True)
class CandidateEvent:
    event_id: str
    source: str
    title: str = ""
    description: str = ""
    occurred_at: str = ""
    camera_name: str = ""
    source_image: str = ""
    image_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    discovered_at: str = field(default_factory=utcnow)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any], source: str = "llmvision") -> "CandidateEvent":
        event_id = clean_text(raw.get("uid") or raw.get("event_id") or raw.get("id"), 256)
        image = clean_text(raw.get("key_frame") or raw.get("image") or raw.get("image_path"), 2048)
        known = {"uid", "event_id", "id", "title", "description", "start", "occurred_at", "camera_name", "key_frame", "image", "image_path"}
        return cls(event_id=event_id, source=source, title=clean_text(raw.get("title"), 512),
                   description=clean_text(raw.get("description")), occurred_at=clean_text(raw.get("start") or raw.get("occurred_at"), 128),
                   camera_name=clean_text(raw.get("camera_name"), 256), source_image=image,
                   metadata={str(k): v for k, v in raw.items() if k not in known and isinstance(v, (str, int, float, bool, type(None)))})

    def as_dict(self) -> dict[str, Any]: return asdict(self)

@dataclass(slots=True)
class Classification:
    event_id: str
    label: str
    classified_at: str = field(default_factory=utcnow)
    updated_at: str = field(default_factory=utcnow)
    candidate: dict[str, Any] = field(default_factory=dict)
    migrated: bool = False

    def as_dict(self) -> dict[str, Any]: return asdict(self)
