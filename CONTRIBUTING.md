# Contributing

Issues and focused pull requests are welcome. Please do not include Home Assistant `.storage` files, images, logs containing tokens, or other private data.

Before submitting a change, run:

```bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -v
node --check custom_components/llm_vision_trainer/frontend/llm-vision-trainer-card.js
python3 scripts/validate.py
```

Keep the integration independent from LLM Vision: do not patch or redistribute LLM Vision code. Mutations must remain backup-first, concurrency-aware, and reversible through quarantine or documented rollback.
