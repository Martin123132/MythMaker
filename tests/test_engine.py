from __future__ import annotations

import unittest

from mythmaker_app.engine import generate_scene
from mythmaker_app.storage import load_default_state


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
        self.assertIn("Scene:", scene["script"])
        self.assertIn("WHY THIS HAPPENED", scene["script"])


if __name__ == "__main__":
    unittest.main()
