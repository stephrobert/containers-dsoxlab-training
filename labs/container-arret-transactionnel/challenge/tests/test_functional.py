"""A single complete verdict, zero until every domain requirement is met."""

from __future__ import annotations

from pathlib import Path

from conftest import lab_host, message


def test_transactional_shutdown_and_forced_abort() -> None:
    probe = Path(__file__).with_name("probe.py").read_text()
    result = lab_host("docker.lab").run(
        "env DSOXLAB_LANG=%s timeout 110 python3 -c %s",
        message(en="en", fr="fr"), probe,
    )
    assert result.rc == 0, message(
        en="The transaction, signal, recovery or forced-abort proof failed: "
        + result.stderr[-900:],
        fr="La preuve transaction, signal, reprise ou abandon forcé échoue : "
        + result.stderr[-900:],
    )
