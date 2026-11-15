# LLM Vision Trainer

> **Beta software — make a full Home Assistant backup before enabling or using any mutation.**

LLM Vision Trainer is an **unofficial, independent companion** for the [LLM Vision](https://github.com/valentinfrlch/ha-llmvision) Home Assistant integration. It helps review image-bearing events, classify examples, and inspect or carefully maintain LLM Vision memory. It is not developed, endorsed, or supported by the LLM Vision project.

The Trainer does **not** modify or redistribute LLM Vision source code. Memory operations update the LLM Vision Settings config entry and associated image files through Home Assistant, after creating a backup. LLM Vision's internal Python and storage interfaces are not public APIs and may change without notice. Initial compatibility testing targets **LLM Vision 1.7.1**.

## Features

- Lovelace card bundled inside the custom integration (no root `www` dependency).
- Automatic Lovelace resource registration in storage mode.
- Review and classify LLM Vision timeline events with authenticated image delivery.
- Separate pending and classified views.
- Inspect memory descriptions, paths, file state, duplicates and cache consistency.
- Edit descriptions, rename or reorder examples, and remove files through quarantine.
- Backup-before-write manifests and concurrent-change detection.
- One-time, non-destructive import of legacy `ring_training.labels` classifications.

## Screenshots

> Screenshots will be added before the stable release.

- Training queue: `docs/screenshots/training-queue.png` (placeholder)
- Memory manager: `docs/screenshots/memory-manager.png` (placeholder)

## Requirements and compatibility

- Home Assistant 2025.1.0 or newer.
- HACS with support for custom integration repositories.
- LLM Vision installed and configured.
- Initially tested with LLM Vision 1.7.1. Other versions may work, but internal timeline/config-entry changes can break compatibility.

## Install with HACS as a custom repository

No repository or release has been published yet. After a GitHub repository and beta release exist:

1. Create a **full Home Assistant backup** and verify that it completed.
2. In HACS, open **Integrations**, choose **Custom repositories**, add this repository URL, and select category **Integration**.
3. Find **LLM Vision Trainer**, install the beta release, and restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and add **LLM Vision Trainer**.
5. Add a manual Lovelace card with:

```yaml
type: custom:llm-vision-trainer-card
```

The integration serves its card from `/llm-vision-trainer/llm-vision-trainer-card.js` and registers that URL automatically when Lovelace uses storage mode. If resources are managed in YAML, add that URL manually as a JavaScript module.

## Configuration

The config flow creates one Trainer instance and records the source integration. Card options include title, maximum visible events, image height, initial panel, and title/description visibility.

Trainer data is stored under Home Assistant's `.storage` directory. Copied event images, backup manifests, and quarantined files remain local to Home Assistant.

## Safety warnings

- **Back up Home Assistant before every first use after an upgrade and before any memory mutation.** The integration's per-operation JSON backup is not a substitute for a Home Assistant backup.
- Description edits, rename, reorder, and deletion change the LLM Vision Settings config entry and/or memory files. They do not modify LLM Vision code.
- Deletion moves an existing image to Trainer quarantine first; it is not immediately erased. Keep quarantine until the result is verified.
- Backups, copied event images, and quarantine consume disk space. Monitor free space and define your own retention/cleanup procedure. No automatic purge is included in this beta.
- LLM Vision internal APIs and data layout may change. Stop using mutation features after an LLM Vision upgrade until compatibility is confirmed.
- Do not expose Home Assistant APIs publicly without normal Home Assistant authentication, TLS, and access controls.

## Existing installations and frontend migration

The card type remains `custom:llm-vision-trainer-card`, so dashboards do not need to be rewritten. Earlier development installs may have a manually copied `www/llm-vision-trainer-card.js` and a resource such as `/local/llm-vision-trainer-card.js` or `/hacsfiles/...`. After installing this beta:

1. Confirm the new resource `/llm-vision-trainer/llm-vision-trainer-card.js` exists under **Settings → Dashboards → Resources**.
2. Remove the old resource only after the card loads from the new URL.
3. Remove the old file from `config/www` only after rollback is no longer needed.
4. Clear the browser cache or reload the frontend if an old card remains cached.

The legacy classification import is idempotent and does not delete the old `ring_training.labels` storage.

## Backup and rollback

Before installation or mutation, create a full Home Assistant backup. For rollback:

1. Disable memory mutations and preserve `.storage/llm_vision_trainer/memory_backups` and `memory_quarantine`.
2. Restore Home Assistant from the pre-change backup, or restore the previous custom component directory and restart Home Assistant.
3. If reverting only a memory operation, inspect the matching timestamped JSON manifest and quarantine file before changing the LLM Vision config entry. Do not edit `.storage` while Home Assistant is running.
4. Re-add the previous Lovelace resource if rolling back to a development build that depended on `config/www`.

## Privacy

All processing is local to Home Assistant unless LLM Vision itself is configured to use a remote model/provider. Trainer APIs require Home Assistant authentication. Event images and memory examples can contain highly sensitive household data; never attach them to public issues. Review backups before sharing because memory descriptions and paths may also reveal private information.

## Development

```bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -v
node --check custom_components/llm_vision_trainer/frontend/llm-vision-trainer-card.js
python3 scripts/validate.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [CHANGELOG.md](CHANGELOG.md), and [docs/RELEASE.md](docs/RELEASE.md).

## Italiano (breve)

LLM Vision Trainer è un companion **non ufficiale** per LLM Vision. Prima dell'installazione e di qualsiasi modifica alla memoria è obbligatorio un backup completo di Home Assistant. Le eliminazioni passano dalla quarantena, ma backup, immagini e quarantena occupano spazio disco. La compatibilità iniziale è stata verificata con LLM Vision 1.7.1; dopo ogni aggiornamento di LLM Vision, considera le funzioni di modifica non verificate finché non vengono ritestate.

## License

MIT — see [LICENSE](LICENSE).
