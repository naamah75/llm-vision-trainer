from pathlib import Path

def test_card_has_separate_sections_and_authenticated_image_path():
    js=Path("custom_components/llm_vision_trainer/frontend/llm-vision-trainer-card.js").read_text()
    assert "Da classificare" in js and "Classificati" in js
    assert "/api/llm_vision_trainer/images/" in js
    assert "ring_training" not in js
    assert "Memoria LLM Vision" in js
    assert "Salva descrizione" in js and "Rinomina" in js and "Elimina" in js
    assert "confirm_external" in js
