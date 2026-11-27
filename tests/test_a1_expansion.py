import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class A1ExpansionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = json.loads((ROOT / "content/a1-expansion.json").read_text())
        cls.course = json.loads((ROOT / "content/course.json").read_text())

    def test_consecutive_a1_weeks_in_both_languages(self):
        for lang in ("lb", "da"):
            units = [unit for unit in self.course["units"]
                     if unit["lang"] == lang and unit["level"] == "A1"]
            self.assertEqual([unit["week"] for unit in units], list(range(1, 21)))
            self.assertEqual(sum(len(unit["lessons"]) for unit in units), 100)

    def test_new_situations_have_distinct_text_and_own_reading(self):
        for lang in ("lb", "da"):
            scenes = [scene for scene in self.scenes if scene["lang"] == lang]
            self.assertEqual(len(scenes), 15)
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
                    self.assertIn("pendiente de revisión", scene["editorial_status"])

    def test_new_lessons_include_recall_and_production_not_only_choices(self):
        for lang in ("lb", "da"):
            lessons = [lesson for unit in self.course["units"]
                       if unit["lang"] == lang and unit["level"] == "A1" and unit["week"] >= 6
                       for lesson in unit["lessons"]]
            self.assertEqual(len(lessons), 75)
            for lesson in lessons:
                with self.subTest(lesson=lesson["id"]):
                    kinds = [task["kind"] for task in lesson["tasks"]]
                    self.assertGreaterEqual(len(kinds), 12)
                    self.assertLessEqual(kinds.count("choice"), 5)
                    self.assertTrue(set(kinds) & {"dictation", "cloze", "writing", "translation", "speaking"})


if __name__ == "__main__":
    unittest.main()
