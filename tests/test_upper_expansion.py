import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Expected gap weeks filled per level (seed units keep their own weeks).
LEVEL_RANGES = {
    "B1": (range(45, 81), {45, 50, 55, 60, 65}),
    "B2": (range(81, 117), {81, 86, 91, 96, 101}),
    "C1": (range(117, 159), {117, 122, 127, 132, 137}),
    "C2": (range(159, 201), {159, 164, 169, 174, 179}),
}


class UpperExpansionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = json.loads((ROOT / "content/upper-expansion.json").read_text())
        cls.course = json.loads((ROOT / "content/course.json").read_text())

    def test_every_week_1_to_200_is_filled_per_language(self):
        for lang in ("lb", "da"):
            weeks = sorted(u["week"] for u in self.course["units"] if u["lang"] == lang)
            self.assertEqual(weeks, list(range(1, 201)),
                             f"{lang}: huecos o duplicados en 1–200")
            lessons = sum(len(u["lessons"]) for u in self.course["units"] if u["lang"] == lang)
            self.assertEqual(lessons, 1000, f"{lang}: se esperan 1000 lecciones")

    def test_gaps_filled_without_moving_seed_units(self):
        for level, (full_range, seeds) in LEVEL_RANGES.items():
            expected_gaps = sorted(set(full_range) - seeds)
            for lang in ("lb", "da"):
                units = [u for u in self.course["units"]
                         if u["lang"] == lang and u["level"] == level]
                self.assertEqual([u["week"] for u in units], sorted(full_range))
                # Seed units keep their fixed weeks and stay non-draft.
                seed_weeks = [u["week"] for u in units if not u.get("editorial_status")]
                self.assertEqual(sorted(seed_weeks), sorted(seeds))
                # New gap-filling units are drafts awaiting native review.
                draft_weeks = [u["week"] for u in units if u.get("editorial_status")]
                self.assertEqual(sorted(draft_weeks), expected_gaps)

    def test_new_scenes_are_distinct_and_well_formed(self):
        for lang in ("lb", "da"):
            scenes = [s for s in self.scenes if s["lang"] == lang]
            self.assertEqual(len(scenes), 136)
            lines = [line["text"] for s in scenes for line in s["dialogue"]]
            self.assertEqual(len(lines), len(set(lines)), f"{lang}: líneas de diálogo repetidas")
            readings = [s["reading"]["text"] for s in scenes]
            self.assertEqual(len(readings), len(set(readings)), f"{lang}: lecturas repetidas")
            for scene in scenes:
                with self.subTest(scene=scene["id"]):
                    self.assertEqual(len(scene["dialogue"]), 4)
                    self.assertNotIn(scene["reading"]["text"],
                                     [line["text"] for line in scene["dialogue"]])
                    self.assertEqual(len(set(scene["reading"]["choices"])), 3)
                    self.assertEqual(scene["listening"]["choices"][scene["listening"]["answer"]],
                                     scene["dialogue"][-1]["es"])
                    self.assertTrue(scene["writing"]["model"])
                    self.assertEqual(scene["course_week"], scene["week"])

    def test_upper_lessons_mix_skills_not_only_choice(self):
        upper = {"B1", "B2", "C1", "C2"}
        for unit in self.course["units"]:
            if unit["level"] not in upper or not unit.get("editorial_status"):
                continue
            for lesson in unit["lessons"]:
                with self.subTest(lesson=lesson["id"]):
                    kinds = [task["kind"] for task in lesson["tasks"]]
                    self.assertTrue(12 <= len(kinds) <= 16)
                    self.assertTrue(set(kinds) & {"dictation", "cloze", "writing",
                                                  "translation", "speaking", "reading"})


if __name__ == "__main__":
    unittest.main()
