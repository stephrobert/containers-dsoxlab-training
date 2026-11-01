"""One verdict covers fresh correlation, measured saturation and safe logs."""

from pathlib import Path

from conftest import lab_host, message


def test_bounded_business_load_and_safe_correlation():
    result = lab_host("docker.lab").run(
        "env DSOXLAB_LANG=%s timeout 110 python3 -c %s",
        message(en="en", fr="fr"),
        Path(__file__).with_name("probe.py").read_text(),
    )
    assert result.rc == 0, message(
        en="The correlation, CPU attribution or safe-log proof failed: "
        + result.stderr[-900:],
        fr="La preuve corrélation, attribution CPU ou journaux sûrs échoue : "
        + result.stderr[-900:],
    )
