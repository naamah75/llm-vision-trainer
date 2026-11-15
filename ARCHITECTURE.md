# Companion architecture

LLM Vision Trainer is an independent, unofficial Home Assistant custom integration. It does not patch, replace or redistribute LLM Vision source code. Its adapter isolates optional LLM Vision timeline/config-entry access so an incompatibility produces a visible Trainer error rather than changing LLM Vision.

Trainer owns its classification registry, copied event images, backup manifests and quarantine. Memory mutations deliberately modify the LLM Vision Settings config entry and related image files through Home Assistant, with validation, concurrency checks and backup-first behavior. These internal interfaces may change.

The Lovelace card is packaged inside `custom_components/llm_vision_trainer/frontend`, served through Home Assistant's asynchronous static-path API, and registered through the Lovelace resource collection in storage mode. YAML resource mode requires manual registration.
