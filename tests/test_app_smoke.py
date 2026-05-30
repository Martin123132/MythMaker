from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
import unittest
from urllib import request


class AppSmokeTests(unittest.TestCase):
    def test_server_doctor_and_generate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env["MYTHMAKER_HOME"] = tmp
            env["MYTHMAKER_DISABLE_OPEN"] = "1"
            proc = subprocess.Popen(
                [sys.executable, "-m", "mythmaker_app.app", "--no-open", "--port", "0"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env,
            )
            try:
                url = self._read_url(proc)
                doctor = self._json(url + "/api/doctor")
                self.assertTrue(doctor["ok"])
                self.assertTrue(doctor["doctor"]["state_ok"])

                started = time.perf_counter()
                generate = self._post_json(
                    url + "/api/generate",
                    {"seed": 5150, "mode": "Bottom House", "weirdness": 75, "cast_size": 4},
                )
                elapsed = time.perf_counter() - started
                self.assertLess(elapsed, 2)
                self.assertTrue(generate["ok"])
                self.assertIn("script", generate["scene"])
                self.assertIn("WHY THIS HAPPENED", generate["scene"]["script"])

                open_exports = self._post_json(url + "/api/open-exports", {})
                self.assertTrue(open_exports["ok"])
                self.assertFalse(open_exports["export_folder"]["opened"])
                self.assertTrue(open_exports["export_folder"]["path"].startswith(tmp))
            finally:
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()

    def _read_url(self, proc: subprocess.Popen[str]) -> str:
        assert proc.stdout is not None
        deadline = time.time() + 8
        while time.time() < deadline:
            line = proc.stdout.readline()
            if not line:
                if proc.poll() is not None:
                    break
                continue
            match = re.search(r"http://127\.0\.0\.1:\d+", line)
            if match:
                return match.group(0)
        self.fail("Server did not print a local URL")

    def _json(self, url: str) -> dict:
        with request.urlopen(url, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, url: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(url, data=data, headers={"content-type": "application/json"}, method="POST")
        with request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
