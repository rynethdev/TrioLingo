import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class A2ExpansionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = json.loads((ROOT / "content/a2-expansion.json").read_text())
        cls.course = json.loads((ROOT / "content/course.json").read_text())

    def test_consecutive_weeks_without_changing_existing_units(self):
        for lang in ("lb", "da"):
            units = [u for u in self.course["units"] if u["lang"] == lang and u["level"] == "A2"]
            self.assertEqual([u["week"] for u in units], list(range(21, 45)))
            self.assertEqual(len(units), 24)
            self.assertEqual(sum(len(u["lessons"]) for u in units), 120)
            self.assertEqual(sum(bool(u.get("editorial_status")) for u in units), 19)
            self.assertEqual([u["week"] for u in units if not u.get("editorial_status")],
                             [21, 26, 31, 36, 41])
            for unit in units:
                if unit.get("editorial_status"):
                    self.assertEqual(unit["id"], f"{lang}-a2-w{unit['week']:02d}")

    def test_new_dialogues_and_readings_are_distinct(self):
        for lang in ("lb", "da"):
            scenes = [scene for scene in self.scenes if scene["lang"] == lang]
            self.assertEqual(len(scenes), 19)
            lines = [line["text"] for scene in scenes for line in scene["dialogue"]]
            self.assertEqual(len(lines), len(set(lines)))
            for scene in scenes:
                with self.subTest(scene=scene["id"]):
                    self.assertEqual(len(scene["dialogue"]), 4)
                    self.assertNotIn(scene["reading"]["text"],
                                     [line["text"] for line in scene["dialogue"]])
                    self.assertEqual(len(set(scene["reading"]["choices"])), 3)
                    self.assertEqual(scene["listening"]["choices"][scene["listening"]["answer"]],
                                     scene["dialogue"][-1]["es"])

    def test_new_lessons_are_not_just_multiple_choice(self):
        for unit in self.course["units"]:
            if unit["level"] != "A2" or not unit.get("editorial_status"):
                continue
            for lesson in unit["lessons"]:
                with self.subTest(lesson=lesson["id"]):
                    kinds = [task["kind"] for task in lesson["tasks"]]
                    self.assertEqual(len(kinds), 13)
                    self.assertLessEqual(kinds.count("choice"), 5)
                    self.assertTrue(set(kinds) & {"dictation", "cloze", "writing", "translation", "speaking"})


if __name__ == "__main__":
    unittest.main()
