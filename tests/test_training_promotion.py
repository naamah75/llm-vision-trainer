import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
API = (ROOT / "custom_components/llm_vision_trainer/api.py").read_text()
MEMORY = (ROOT / "custom_components/llm_vision_trainer/memory.py").read_text()
STORE = (ROOT / "custom_components/llm_vision_trainer/store.py").read_text()
CARD = (ROOT / "custom_components/llm_vision_trainer/frontend/llm-vision-trainer-card.js").read_text()

class TrainingPromotionContractTests(unittest.TestCase):
    def test_promotes_before_classifying(self):
        ast.parse(API)
        self.assertLess(API.index("rt.memory.promote"), API.index("rt.store.classify"))
        self.assertIn("rollback_promotion", API)

    def test_candidate_lookup_is_non_destructive(self):
        ast.parse(STORE)
        block = STORE[STORE.index("async def candidate_for"):STORE.index("async def upsert_candidates")]
        self.assertNotIn("pop(", block)

    def test_memory_transaction_has_backup_and_file_rollback(self):
        ast.parse(MEMORY)
        self.assertIn('_commit(entry, snap, "training", original)', MEMORY)
        self.assertIn("_unlink_if_exists", MEMORY)
        self.assertIn("training-rollback", MEMORY)

    def test_frontend_registration_is_idempotent(self):
        self.assertIn("customElements.get('llm-vision-trainer-card')", CARD)
        self.assertIn("window.customCards.some", CARD)

if __name__ == "__main__": unittest.main()
