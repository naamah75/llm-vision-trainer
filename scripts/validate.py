"""Dependency-free repository validation used locally and in reviews."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
for path in ROOT.rglob("*.json"):
    if ".git" not in path.parts:
        json.loads(path.read_text(encoding="utf-8"))
manifest = json.loads((ROOT / "custom_components/llm_vision_trainer/manifest.json").read_text())
assert manifest["version"] == "0.1.0-beta.2"
assert (ROOT / "custom_components/llm_vision_trainer/frontend/llm-vision-trainer-card.js").is_file()
assert not (ROOT / "www").exists(), "The HACS package must not depend on a root www directory"
print("JSON and package layout validation passed")
