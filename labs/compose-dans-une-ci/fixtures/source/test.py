import json
import os
from pathlib import Path
from urllib.request import urlopen

with urlopen("http://api:8080/value", timeout=5) as response:
    observed = response.read().decode().strip()
expected = os.environ["EXPECTED_VALUE"].strip()
passed = observed == expected and os.environ.get("TEST_FAIL", "0") == "0"
Path("/artifacts/result.json").write_text(json.dumps({
    "observed": observed, "expected": expected, "passed": passed,
}))
raise SystemExit(0 if passed else 1)
