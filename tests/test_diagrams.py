import hashlib
import subprocess
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SVG_DIR = ROOT / "docs" / "images"
SVG_FILES = [
    "overview.svg",
    "guardrail-flow.svg",
    "briefing-flow.svg",
]


class DiagramFiles(unittest.TestCase):
    def read(self, name):
        path = SVG_DIR / name
        self.assertTrue(path.exists(), f"missing {path}")
        return path.read_bytes()

    def labels(self, name, expected):
        data = self.read(name).decode("ascii")
        for label in expected:
            self.assertIn(label, data, f"{name} missing {label}")

    def test_each_svg_parses_and_has_viewbox(self):
        for name in SVG_FILES:
            data = self.read(name).decode("ascii")
            self.assertTrue(data.isascii(), f"{name}: non-ASCII")
            root = ET.fromstring(data)
            self.assertEqual(root.tag.split("}")[-1], "svg")
            vb = root.get("viewBox")
            self.assertTrue(vb, f"{name}: no viewBox")
            parts = vb.split()
            self.assertEqual(len(parts), 4, f"{name}: bad viewBox")
            self.assertAlmostEqual(float(parts[2]), 1000.0, delta=1.0, msg=f"{name}: width not ~1000")
            # solid background rect spanning the canvas (readable in any GitHub theme)
            rects = [e for e in root.iter() if e.tag.split("}")[-1] == "rect"]
            self.assertTrue(rects[0].get("fill", "").startswith("#"), f"{name}: no solid background rect")
            self.assertEqual(rects[0].get("width"), "1000", f"{name}: background does not span the canvas")
            text = data.lower()
            # The standard SVG namespace declaration is allowed; any other
            # http(s) reference is not.
            check = text.replace('xmlns="http://www.w3.org/2000/svg"', "")
            self.assertNotIn("<script", check)
            self.assertNotIn("<foreignobject", check)
            self.assertNotIn("http://", check)
            self.assertNotIn("https://", check)

    def test_overview_labels(self):
        self.labels("overview.svg", ("select-controls.py", "SPECIALIST_MODEL", "JUDGE_MODEL",
                                     "policy.json", "grounded", "catalog-default", "excluded"))

    def test_guardrail_labels(self):
        self.labels("guardrail-flow.svg", ("select-controls.py", "SPECIALIST_MODEL", "JUDGE_MODEL",
                                           "REVIEWER_MODEL", "check-policy.py", "policy.json",
                                           "exceptions.md", "Bedrock", "NeMo"))

    def test_briefing_labels(self):
        self.labels("briefing-flow.svg", ("run.sh", "RESEARCH_MODEL", "JUDGE_MODEL", "WRITER_MODEL",
                                          "check-briefing.sh"))

    def test_regeneration_is_deterministic(self):
        before = {name: hashlib.sha256(self.read(name)).digest() for name in SVG_FILES}
        proc = subprocess.run(
            ["python3", "scripts/make-diagrams.py"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for name in SVG_FILES:
            after = hashlib.sha256((SVG_DIR / name).read_bytes()).digest()
            self.assertEqual(before[name], after, f"{name} not reproducible; run: python3 scripts/make-diagrams.py")


if __name__ == "__main__":
    unittest.main()
