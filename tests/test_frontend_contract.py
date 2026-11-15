import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = (ROOT / "custom_components/llm_vision_trainer/frontend.py").read_text()


class FrontendContractTests(unittest.TestCase):
    def test_uses_modern_static_paths_and_resource_collection(self):
        ast.parse(SOURCE)
        self.assertIn("async_register_static_paths", SOURCE)
        self.assertIn("StaticPathConfig", SOURCE)
        self.assertIn("async_create_item", SOURCE)
        self.assertNotIn("add_extra_js_url", SOURCE)

    def test_loads_resource_collection_before_inspection_or_write(self):
        self.assertLess(SOURCE.index("resources.async_load()"), SOURCE.index("resources.async_items()"))
        self.assertLess(SOURCE.index("resources.async_items()"), SOURCE.index("resources.async_create_item"))

    def test_card_is_packaged_inside_custom_component(self):
        self.assertTrue((ROOT / "custom_components/llm_vision_trainer/frontend/llm-vision-trainer-card.js").is_file())
        self.assertFalse((ROOT / "www").exists())


if __name__ == "__main__":
    unittest.main()
