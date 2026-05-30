from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest


class StorageTests(unittest.TestCase):
    def test_storage_saves_state_and_favourite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_home = os.environ.get("MYTHMAKER_HOME")
            os.environ["MYTHMAKER_HOME"] = tmp
            try:
                from mythmaker_app import storage

                state = storage.load_default_state()
                state["characters"][0]["name"] = "Test Character"
                saved = storage.save_state(state)
                loaded = storage.load_state()
                self.assertEqual(saved["characters"][0]["name"], "Test Character")
                self.assertEqual(loaded["characters"][0]["name"], "Test Character")

                item = storage.save_favourite({"title": "Tiny Myth", "script": "Scene body", "seed": 9})
                favourites = storage.list_favourites()
                self.assertEqual(favourites[0]["id"], item["id"])

                exported = storage.export_scene({"title": "Tiny Myth", "script": "Scene body"}, "txt")
                self.assertTrue(Path(exported["path"]).exists())
                self.assertTrue(str(exported["path"]).startswith(tmp))

                exported_html = storage.export_scene({"title": "Tiny Myth", "script": "Scene body"}, "html")
                self.assertTrue(Path(exported_html["path"]).exists())
                self.assertEqual(exported_html["format"], "html")

                opened_paths = []
                result = storage.open_exports_folder(opener=lambda path: opened_paths.append(path))
                self.assertTrue(result["opened"])
                self.assertEqual(opened_paths[0], Path(tmp, "exports").resolve())
                self.assertTrue(str(opened_paths[0]).startswith(tmp))

                blocked = storage.open_exports_folder(opener=lambda path: (_ for _ in ()).throw(OSError("blocked")))
                self.assertFalse(blocked["opened"])
                self.assertIn("blocked", blocked["error"])
            finally:
                if old_home is None:
                    os.environ.pop("MYTHMAKER_HOME", None)
                else:
                    os.environ["MYTHMAKER_HOME"] = old_home


if __name__ == "__main__":
    unittest.main()
