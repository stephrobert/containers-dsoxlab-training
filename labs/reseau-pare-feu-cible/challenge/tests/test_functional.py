"""One verdict covers all hops and preserved protections after recreation."""

from pathlib import Path

from conftest import lab_host, message


def test_targeted_firewall_and_denied_paths():
    result = lab_host("docker.lab").run(
        "env DSOXLAB_LANG=%s timeout 110 python3 -c %s",
        message(en="en", fr="fr"),
        Path(__file__).with_name("probe.py").read_text(),
    )
    assert result.rc == 0, message(
        en="The multi-hop or protected-path proof failed: " + result.stderr[-900:],
        fr="La preuve multi-sauts ou chemins protégés échoue : " + result.stderr[-900:],
    )
