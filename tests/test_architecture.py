import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class ArchitectureDoc(unittest.TestCase):
    def test_diagrams_are_embedded(self):
        text = (ROOT / "docs" / "architecture.md").read_text(encoding="utf-8")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("images/guardrail-flow.svg", text)
        self.assertIn("images/briefing-flow.svg", text)
        self.assertIn("docs/images/overview.svg", readme)
        self.assertNotIn("```mermaid", text + readme, "old Mermaid diagrams should be gone")

    def test_every_named_file_exists(self):
        for rel in ("scripts/guardrail.py", "scripts/check-policy.py", "bench/guardrail/check-golden.sh",
                    "bench/guardrail/run-live.sh", "bench/guardrail/record.py", "schemas/policy.schema.json",
                    "seeds/guardrail-catalog.json"):
            self.assertTrue((ROOT / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
