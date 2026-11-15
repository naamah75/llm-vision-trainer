import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = (ROOT / "custom_components/llm_vision_trainer/memory.py").read_text()

class MemoryManagerContractTests(unittest.TestCase):
    def test_module_parses_without_private_llmvision_imports(self):
        tree = ast.parse(SOURCE)
        imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        self.assertFalse(any((name or "").startswith("custom_components.llmvision") for name in imports))

    def test_parallel_array_and_safety_contract(self):
        self.assertIn('(\"memory_paths\", \"memory_strings\", \"images\")', SOURCE)
        for marker in ("confirm_external", "_move_to_quarantine", "_write_backup", "_SAFE_NAME.fullmatch", "async_update_entry", "MemoryConflict"):
            self.assertIn(marker, SOURCE)

    def test_backup_precedes_config_update(self):
        self.assertLess(SOURCE.index("self._write_backup"), SOURCE.index("async_update_entry"))

if __name__ == "__main__": unittest.main()
