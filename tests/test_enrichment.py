import collections
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class EnrichmentTest(unittest.TestCase):
    """Weeks with content/enrichment/wNNN.json must carry that material into
    the course and stop recycling the same question across the unit."""

    @classmethod
    def setUpClass(cls):
        cls.files = sorted((ROOT / "content/enrichment").glob("w*.json"))
        cls.scenes = {s["id"]: s for s in json.loads((ROOT / "content/upper-expansion.json").read_text())}
        cls.units = {u["id"]: u for u in json.loads((ROOT / "content/course.json").read_text())["units"]}

    def enriched_ids(self):
        for path in self.files:
            week = json.loads(path.read_text())["week"]
            for lang in ("lb", "da"):
                yield next(sid for sid, s in self.scenes.items()
                           if s["lang"] == lang and s["week"] == week)

    def test_files_cover_both_languages_and_reach_the_scene(self):
        for path in self.files:
            data = json.loads(path.read_text())
            self.assertEqual(path.name, f"w{data['week']:03d}.json")
            for lang in ("lb", "da"):
                self.assertIn(lang, data, f"{path.name}: falta {lang}")
        for sid in self.enriched_ids():
            self.assertIn("enrichment", self.scenes[sid], f"{sid}: enriquecimiento no integrado")

    def test_enriched_units_use_the_second_conversation(self):
        for sid in self.enriched_ids():
            tasks = [t for l in self.units[sid]["lessons"] for t in l["tasks"]]
            line2 = [t for t in tasks if "-line2-" in json.dumps(t)]
            self.assertGreaterEqual(len(line2), 3, f"{sid}: segunda conversación sin usar")

    def test_enriched_units_do_not_repeat_tasks(self):
        for sid in self.enriched_ids():
            for lesson in self.units[sid]["lessons"]:
                self.assertTrue(12 <= len(lesson["tasks"]) <= 16, lesson["id"])
            pairs = collections.Counter(
                (t["prompt"], str(t.get("answer")))
                for l in self.units[sid]["lessons"] for t in l["tasks"] if t["kind"] != "review")
            self.assertLessEqual(max(pairs.values()), 2, f"{sid}: una tarea se repite más de dos veces")


if __name__ == "__main__":
    unittest.main()
