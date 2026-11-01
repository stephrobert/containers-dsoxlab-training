"""Local stdlib-only author tests; never invoke pytest or contact a VM."""

import concurrent.futures
import contextlib
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SERVICE = ROOT / "fixtures/service.py"


def get(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=4) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.load(error)


def wait(predicate):
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        try:
            result = predicate()
            if result:
                return result
        except OSError:
            pass
        time.sleep(0.025)
    raise AssertionError("Local author barrier timed out")


class TransactionTests(unittest.TestCase):
    def test_real_http_graceful_forced_and_configuration_comparison(self):
        database = ROOT / "author_tests" / ("trial-" + uuid.uuid4().hex + ".sqlite")
        process = None
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:

            def start(mode):
                nonlocal process
                with socket.socket() as listener:
                    listener.bind(("127.0.0.1", 0))
                    port = listener.getsockname()[1]
                process = subprocess.Popen(
                    [sys.executable, str(SERVICE)],
                    env={
                        **os.environ,
                        "DATABASE": str(database),
                        "PORT": str(port),
                        "SERVICE_MODE": mode,
                    },
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                base = f"http://127.0.0.1:{port}"
                wait(lambda: get(base, "/health")[0] == 200)
                self.assertEqual(
                    get(base, "/configuration"), (200, {"service_mode": mode})
                )
                return base

            def held(base, key):
                future = pool.submit(get, base, "/write?id=" + key)
                wait(lambda: get(base, "/inflight")[1] == {"id": key, "begun": True})
                self.assertFalse(future.done())
                self.assertEqual(get(base, "/record?id=" + key)[0], 404)
                return future

            try:
                base = start("first")
                good = uuid.uuid4().hex
                future = held(base, good)
                process.send_signal(signal.SIGTERM)
                self.assertEqual(
                    future.result(timeout=4), (200, {"id": good, "value": "accepted"})
                )
                logs, errors = process.communicate(timeout=4)
                self.assertEqual(process.returncode, 0, errors)
                events = [json.loads(line) for line in logs.splitlines()]
                self.assertEqual(
                    [e["event"] for e in events],
                    [
                        "ready",
                        "transaction_started",
                        "signal_received",
                        "transaction_committed",
                        "request_finished",
                        "drained",
                    ],
                )
                base = start("second")
                self.assertEqual(
                    get(base, "/record?id=" + good)[1]["value"], "accepted"
                )
                lost = uuid.uuid4().hex
                future = held(base, lost)
                process.kill()
                with self.assertRaises(OSError):
                    future.result(timeout=4)
                logs, _ = process.communicate(timeout=4)
                self.assertEqual(process.returncode, -signal.SIGKILL)
                self.assertNotIn("transaction_committed", logs)
                base = start("third")
                self.assertEqual(get(base, "/record?id=" + lost)[0], 404)
                self.assertEqual(
                    get(base, "/record?id=" + good)[1]["value"], "accepted"
                )
                future = held(base, uuid.uuid4().hex)
                get(base, "/release")
                self.assertEqual(future.result(timeout=4)[0], 200)
            finally:
                if process and process.poll() is None:
                    process.kill()
                    process.communicate(timeout=4)
                for suffix in ("", "-journal", "-wal", "-shm"):
                    with contextlib.suppress(FileNotFoundError):
                        Path(str(database) + suffix).unlink()

    def test_supplied_launcher_leaves_a_child_as_pid_one_waiter(self):
        source = (ROOT / "fixtures/entry.sh").read_text()
        self.assertIn("python /app/service.py &", source)
        self.assertNotIn("exec python", source)

    def test_cleanup_preserves_canonical_preexisting_objects_and_images(self):
        spec = importlib.util.spec_from_file_location(
            "owned_lifecycle", ROOT / "fixtures/lifecycle.py"
        )
        lifecycle = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(lifecycle)
        prefix = "dsoxlab-container-arret-transactionnel-"
        baseline = {
            "images": ["sha256:baseline"],
            "resources": {
                "container": ["full-preexisting"],
                "network": ["network-preexisting"],
                "volume": [prefix + "old-data"],
            },
        }
        state = Mock()
        state.exists.return_value = True
        state.read_text.return_value = json.dumps(baseline)
        calls = []

        def docker(*args):
            calls.append(args)
            if args[:2] == ("ps", "-aq"):
                return "short-old short-new"
            if args[:3] == ("network", "ls", "-q"):
                return "short-network"
            if args[:3] == ("volume", "ls", "-q"):
                return prefix + "old-data"
            if args[:3] == ("image", "ls", "-q"):
                return "sha256:baseline"
            if args[:2] == ("container", "inspect"):
                return json.dumps(
                    [
                        {
                            "Name": prefix + "container",
                            "Id": "full-preexisting"
                            if args[2] == "short-old"
                            else "full-created",
                        }
                    ]
                )
            if args[:2] == ("network", "inspect"):
                return json.dumps(
                    [{"Name": prefix + "network", "Id": "network-preexisting"}]
                )
            if args[:2] == ("volume", "inspect"):
                return json.dumps([{"Name": prefix + "old-data"}])
            if args[:2] == ("container", "rm"):
                return ""
            raise AssertionError("Unexpected destructive lifecycle operation")

        image_inspect = Mock(
            returncode=0, stdout=json.dumps([{"Id": "sha256:baseline"}])
        )
        with (
            patch.object(lifecycle, "STATE", state),
            patch.object(lifecycle, "PREFIX", prefix),
            patch.object(lifecycle, "docker", side_effect=docker),
            patch.object(lifecycle.subprocess, "run", return_value=image_inspect),
        ):
            lifecycle.cleanup()
        self.assertEqual(
            [call for call in calls if "rm" in call],
            [("container", "rm", "-f", "short-new")],
        )


if __name__ == "__main__":
    unittest.main()
