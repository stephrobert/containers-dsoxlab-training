"""Local application behavior only: no Docker, pytest replay or VM."""

import concurrent.futures
import contextlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "correlation_probe", ROOT / "challenge/tests/probe.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class CorrelationTests(unittest.TestCase):
    def test_fresh_end_to_end_business_responses_and_no_header_leak(self):
        processes = []

        def start(role, safe, correlate, upstream=""):
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            process = subprocess.Popen(
                [sys.executable, str(ROOT / "fixtures/service.py")],
                env={
                    **os.environ,
                    "ROLE": role,
                    "PORT": str(port),
                    "SAFE_LOGS": safe,
                    "CORRELATE": correlate,
                    "UPSTREAM": upstream,
                },
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            processes.append(process)
            base = f"http://127.0.0.1:{port}"
            deadline = time.monotonic() + 4
            while True:
                try:
                    with urllib.request.urlopen(base + "/health", timeout=1):
                        return base
                except OSError:
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.025)

        def stop(process):
            process.terminate()
            out, _ = process.communicate(timeout=4)
            return out

        try:
            worker = start("worker", "1", "1")
            gateway = start("gateway", "1", "1", worker)
            witness = uuid.uuid4().hex
            identities = [uuid.uuid4().hex for _ in range(4)]
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = [
                    pool.submit(probe.request, gateway, rid, i + 1, witness)
                    for i, rid in enumerate(identities)
                ]
                for i, future in enumerate(futures):
                    self.assertEqual(
                        future.result(timeout=4),
                        (
                            200,
                            {
                                "request_id": identities[i],
                                "quantity": i + 1,
                                "total_cents": (i + 1) * 125,
                            },
                        ),
                    )
            self.assertEqual(
                probe.request(gateway, uuid.uuid4().hex, 0, witness),
                (400, {"error": "invalid_quote"}),
            )
            for role, process in zip(("worker", "gateway"), processes, strict=True):
                logs = stop(process)
                self.assertNotIn(witness, logs)
                self.assertNotIn("authorization", logs.lower())
                records = [json.loads(line) for line in logs.splitlines()]
                self.assertEqual({r["request_id"] for r in records}, set(identities))
                self.assertTrue(all(r["component"] == role for r in records))
            unsafe = start("worker", "0", "1")
            rid = uuid.uuid4().hex
            self.assertEqual(
                probe.request(unsafe, rid, 2, witness)[1]["request_id"], rid
            )
            logs = stop(processes[-1])
            self.assertIn(witness, logs)
            self.assertIn("authorization", logs.lower())
            uncorrelated = start("worker", "1", "0")
            self.assertNotEqual(
                probe.request(uncorrelated, rid, 2, witness)[1]["request_id"], rid
            )
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                with contextlib.suppress(OSError):
                    process.communicate(timeout=4)


if __name__ == "__main__":
    unittest.main()
