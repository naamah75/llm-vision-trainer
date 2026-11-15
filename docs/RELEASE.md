# Release checklist

## Before publishing

- [ ] Decide and create the public GitHub repository; update manifest documentation/issue URLs and `codeowners` if the final owner differs.
- [ ] Confirm the repository default branch and protect secrets/private files.
- [ ] Run `python3 -m compileall -q custom_components tests`.
- [ ] Parse all JSON with `python3 scripts/validate.py`.
- [ ] Run `node --check custom_components/llm_vision_trainer/frontend/llm-vision-trainer-card.js`.
- [ ] Run `python3 -m unittest discover -s tests -v`.
- [ ] Run HACS Action and Hassfest successfully on GitHub Actions.
- [ ] Test a clean HACS custom-repository installation on a disposable Home Assistant instance.
- [ ] Verify the card resource is created without changing or removing existing Lovelace resources.
- [ ] Test read-only behavior against LLM Vision 1.7.1.
- [ ] With a fresh full HA backup, test description, rename, reorder, deletion/quarantine, rollback and disk-space behavior.
- [ ] Add real screenshots with private details removed.
- [ ] Review the changelog and confirm manifest version `0.1.0-beta.1`.
- [ ] Create tag `v0.1.0-beta.1` and a GitHub prerelease; do not mark stable.

## Draft release text: v0.1.0-beta.1

### LLM Vision Trainer 0.1.0-beta.1

First public beta of an **unofficial LLM Vision companion** for Home Assistant. It bundles a Lovelace training card, event classification, authenticated local image handling, and a cautious memory manager with backup-before-write and quarantine deletion.

**Compatibility:** initially tested with LLM Vision 1.7.1. LLM Vision internal interfaces may change and are not guaranteed APIs.

**Before installing:** create and verify a full Home Assistant backup. Memory edits update the LLM Vision Settings config entry and related image files, without modifying LLM Vision source code. Keep quarantine and monitor disk usage.

Install as a HACS custom integration repository, restart Home Assistant, add the integration, then use `type: custom:llm-vision-trainer-card`. This is prerelease software; please report issues with private images, tokens and `.storage` data removed.

## Local-only material

The `reference/` directory contains development prototypes and is intentionally excluded by `.gitignore`; it must not be included in a public repository, HACS download, or release archive.
