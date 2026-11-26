# Changelog

## 0.1.0-beta.2

- Promote confirmed classifications into LLM Vision memory with backup-before-write and rollback.
- Keep candidates queued when memory promotion fails.
- Make Lovelace custom-element registration idempotent.

All notable changes are documented here. This project follows Semantic Versioning.

## [0.1.0-beta.1] - Unreleased

### Added
- First HACS-installable beta custom integration.
- Bundled and automatically registered Lovelace card.
- Authenticated event classification and image endpoints.
- LLM Vision memory inspection, backup-before-write editing, rename, reorder and quarantine deletion.
- One-time import of legacy `ring_training.labels` classifications.

### Compatibility
- Initially tested against LLM Vision 1.7.1. Internal LLM Vision interfaces may change.
