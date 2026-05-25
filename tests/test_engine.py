from __future__ import annotations

import unittest

from mythmaker_app.engine import generate_scene
from mythmaker_app.storage import load_default_state
from scripts.sample_scenes import DEMO_RUNS


class EngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = load_default_state()

    def test_same_seed_produces_same_scene(self) -> None:
        options = {"seed": 12345, "mode": "Bottom House", "weirdness": 60, "cast_size": 4}
        first = generate_scene(self.state, options)
        second = generate_scene(self.state, options)
        self.assertEqual(first["script"], second["script"])
        self.assertEqual(first["cast"], second["cast"])

    def test_different_seed_changes_scene(self) -> None:
        first = generate_scene(self.state, {"seed": 111, "mode": "Bottom House"})
        second = generate_scene(self.state, {"seed": 222, "mode": "Bottom House"})
        self.assertNotEqual(first["script"], second["script"])

    def test_weirdness_changes_drift_profile(self) -> None:
        low = generate_scene(self.state, {"seed": 9876, "mode": "Bottom House", "weirdness": 5})
        high = generate_scene(self.state, {"seed": 9876, "mode": "Bottom House", "weirdness": 95})
        low_drifts = [item["drift_type"] for item in low["cast"]]
        high_drifts = [item["drift_type"] for item in high["cast"]]
        self.assertNotEqual(low_drifts, high_drifts)

    def test_prime_traces_have_seven_steps(self) -> None:
        scene = generate_scene(self.state, {"seed": 7, "cast_size": 5})
        for item in scene["cast"]:
            self.assertEqual(len(item["trace"]), 7)

    def test_scene_has_required_sections(self) -> None:
        scene = generate_scene(self.state, {"seed": 42})
        self.assertTrue(scene["title"])
        self.assertTrue(scene["setting"])
        self.assertTrue(scene["script"])
        self.assertTrue(scene["trace_lines"])
        self.assertTrue(scene["beats"])
        self.assertTrue(scene["callback"])
        self.assertIn("Cast:", scene["script"])
        self.assertIn("Cold Open:", scene["script"])
        self.assertIn("Scene:", scene["script"])
        self.assertIn("Callback:", scene["script"])
        self.assertIn("WHY THIS HAPPENED", scene["script"])

    def test_demo_seeds_render_without_placeholder_text(self) -> None:
        bad_fragments = ["TODO", "FIXME", "undefined", "lorem ipsum"]
        for seed, mode, weirdness, cast_size in DEMO_RUNS:
            with self.subTest(seed=seed, mode=mode):
                scene = generate_scene(
                    self.state,
                    {"seed": seed, "mode": mode, "weirdness": weirdness, "cast_size": cast_size},
                )
                self.assertIn("Closing Sting:", scene["script"])
                self.assertIn("Callback chosen:", "\n".join(scene["trace_lines"]))
                self.assertEqual(len(scene["cast"]), cast_size)
                for fragment in bad_fragments:
                    self.assertNotIn(fragment, scene["script"])

    def test_mode_specific_beats_are_present(self) -> None:
        expectations = {
            "Therapy Under The Stairs": "GPT Under The Stairs: And how long",
            "Five-a-Side": "The Referee of Truth: Whistle.",
            "Cult Drift": "Auntie Brenda of the Remote: I've seen better cults",
        }
        for mode, expected in expectations.items():
            with self.subTest(mode=mode):
                scene = generate_scene(self.state, {"seed": 1234, "mode": mode, "weirdness": 80})
                self.assertIn(expected, scene["script"])


if __name__ == "__main__":
    unittest.main()
