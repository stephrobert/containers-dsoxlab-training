"""Local structural constraints; real forwarding awaits VM authorization."""

import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "firewall_probe", ROOT / "challenge/tests/probe.py"
)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class TopologyTests(unittest.TestCase):
    def test_fixture_is_isolated_and_has_a_real_wrong_business_rule(self):
        config = yaml.safe_load((ROOT / "fixtures/compose.yaml").read_text())
        self.assertEqual(
            set(config["services"]), {"router", "allowed", "denied", "server"}
        )
        self.assertEqual(len(config["networks"]), 2)
        for network in config["networks"].values():
            self.assertEqual(network["labels"]["dsoxlab.lab"], "reseau-pare-feu-cible")
        for service in config["services"].values():
            self.assertEqual(service["cap_add"], ["NET_ADMIN"])
            self.assertEqual(service["cap_drop"], ["ALL"])
            self.assertNotIn("privileged", service)
            self.assertNotIn("ports", service)
            self.assertNotIn("network_mode", service)
            self.assertEqual(service["labels"]["dsoxlab.lab"], "reseau-pare-feu-cible")
        rules = (ROOT / "fixtures/rules.nft").read_text()
        self.assertIn('tcp dport 8089 counter accept comment "business"', rules)
        self.assertEqual(rules.count("policy drop"), 2)
        self.assertIn('counter drop comment "deny-untrusted"', rules)
        self.assertIn('counter drop comment "deny-debug"', rules)

    def test_protection_checker_refuses_blanket_removal(self):
        payload = {
            "nftables": [
                {"chain": {"name": "input", "policy": "accept"}},
                {"chain": {"name": "forward", "policy": "accept"}},
            ]
        }
        with (
            patch.object(probe, "docker", return_value=json.dumps(payload)),
            self.assertRaises(AssertionError),
        ):
            probe.protections({"Id": "local-mock"})
        payload["nftables"][0]["chain"]["policy"] = "drop"
        payload["nftables"][1]["chain"]["policy"] = "drop"
        with (
            patch.object(probe, "docker", return_value=json.dumps(payload)),
            self.assertRaises(AssertionError),
        ):
            probe.protections({"Id": "local-mock"})


if __name__ == "__main__":
    unittest.main()
