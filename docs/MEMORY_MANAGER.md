# LLM Vision memory manager

The beta targets the three parallel memory arrays observed in LLM Vision 1.7.1: `memory_paths`, `memory_strings`, and `images`. This is an internal compatibility boundary, not a guaranteed LLM Vision API. The Trainer does not patch LLM Vision code.

Authenticated endpoints expose listing, thumbnails and the `description`, `rename`, `reorder`, and `delete` actions. Before a mutation, the manager validates array cardinality, detects concurrent changes, and writes a timestamped JSON manifest under `.storage/llm_vision_trainer/memory_backups`. Deletion first moves an existing image into `.storage/llm_vision_trainer/memory_quarantine`; an external file requires explicit confirmation.

A full Home Assistant backup is mandatory before using mutations. Per-operation manifests and quarantine support investigation and rollback but are not full backups. Both directories can grow indefinitely in this beta, so monitor free disk space and retain files only as long as needed. Never hand-edit `.storage` while Home Assistant is running.
