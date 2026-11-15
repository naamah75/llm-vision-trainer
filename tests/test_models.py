import importlib.util
import unittest
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "custom_components" / "llm_vision_trainer" / "models.py"
spec = importlib.util.spec_from_file_location("llm_vision_trainer_models", MODULE_PATH)
models = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = models
spec.loader.exec_module(models)
CandidateEvent = models.CandidateEvent
Classification = models.Classification

class ModelTests(unittest.TestCase):
    def test_candidate_normalizes_timeline_event(self):
        event = CandidateEvent.from_mapping({"uid": "abc", "title": " Door ", "key_frame": "/media/a.jpg", "extra": 3})
        self.assertEqual(event.event_id, "abc")
        self.assertEqual(event.title, "Door")
        self.assertTrue(event.source_image.endswith("a.jpg"))
        self.assertEqual(event.metadata, {"extra": 3})

    def test_classification_is_json_ready(self):
        item = Classification("abc", "amazon", candidate={"event_id": "abc"}).as_dict()
        self.assertEqual(item["label"], "amazon")
        self.assertEqual(item["candidate"]["event_id"], "abc")

if __name__ == "__main__":
    unittest.main()
