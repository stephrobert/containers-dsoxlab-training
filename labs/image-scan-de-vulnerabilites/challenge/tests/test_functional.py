"""Compare learner evidence with fresh, real offline debsecan output."""

from __future__ import annotations

import datetime
import json
import uuid

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-image-scan"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _report(host, image, filename):
    path = f"{ROOT}/{filename}"
    result = host.run("/usr/bin/python3 %s/scan.py %s %s", ROOT, image, path)
    report = host.run("cat %s", path)
    assert report.rc == 0 and result.rc in (0, 1), message(
        en="Produce a real debsecan report; scanner errors are not policy verdicts.",
        fr="Produisez un vrai rapport debsecan ; une erreur de scan n'est pas un verdict.",
    )
    return result.rc, json.loads(report.stdout)


def _evidence(host, name):
    stored = host.run("cat %s/%s.json", ROOT, name)
    assert stored.rc == 0, message(
        en=f"Create the dated {name}.json scan evidence.",
        fr=f"Créez la preuve de scan datée {name}.json.",
    )
    data = json.loads(stored.stdout)
    when = datetime.datetime.fromisoformat(data["scanned_at"])
    age = datetime.datetime.now(datetime.UTC) - when
    assert datetime.timedelta(0) <= age < datetime.timedelta(hours=24), message(
        en="Evidence must be dated within the last 24 hours, not a timeless claim.",
        fr="La preuve doit dater de moins de 24 heures, pas être une affirmation intemporelle.",
    )
    return data


def test_legacy_evidence_matches_real_scanner_findings(host):
    evidence = _evidence(host, "legacy-report")
    code, fresh = _report(host, "dsoxlab-scan:legacy", "verify-legacy.json")
    assert code == 1 and "CVE-2023-0286" in fresh["output"], message(
        en="The genuine legacy fixture must demonstrate CVE-2023-0286.",
        fr="La vraie fixture ancienne doit démontrer CVE-2023-0286.",
    )
    assert all(evidence[k] == fresh[k] for k in (
        "image_id", "database_sha256", "database_date", "scanner",
        "status_sha256", "output", "policy_cve", "blocked",
    )), message(
        en="Retain unmodified scanner output and bind it to image ID and database hash.",
        fr="Gardez la sortie scanner complète, liée à l'ID d'image et au hash de base.",
    )


def test_candidate_is_corrected_genuine_library_and_report_is_true(host):
    evidence = _evidence(host, "candidate-report")
    code, fresh = _report(host, "dsoxlab-scan:candidate", "verify-candidate.json")
    fixed = host.run("docker image inspect --format '{{.Id}}' dsoxlab-scan:fixed")
    assert code == 0 and fresh["image_id"] == fixed.stdout.strip(), message(
        en="Promote the supplied corrected genuine package image, not an empty inventory.",
        fr="Promouvez l'image du vrai paquet corrigé fourni, pas un inventaire vide.",
    )
    assert all(evidence[k] == fresh[k] for k in (
        "image_id", "database_sha256", "database_date", "scanner",
        "status_sha256", "output", "policy_cve", "blocked",
    )), message(
        en="Candidate evidence must match a fresh scan, including other findings.",
        fr="La preuve candidate doit correspondre au scan frais, autres alertes comprises.",
    )


def test_gate_rejects_legacy_and_accepts_fixed_from_fresh_scans(host):
    _evidence(host, "candidate-report")
    for image, expected in (("legacy", 1), ("fixed", 0)):
        filename = f"gate-trial-{uuid.uuid4().hex}.json"
        path = f"{ROOT}/{filename}"
        try:
            result = host.run("%s/gate.sh dsoxlab-scan:%s %s", ROOT, image, path)
            evidence = host.run("cat %s", path)
            assert result.rc == expected and evidence.rc == 0, message(
                en="gate.sh IMAGE REPORT must scan now and propagate the CVE policy verdict.",
                fr="gate.sh IMAGE RAPPORT doit scanner maintenant et propager le verdict CVE.",
            )
            _, fresh = _report(host, f"dsoxlab-scan:{image}", f"verify-{image}.json")
            generated = json.loads(evidence.stdout)
            assert all(generated[k] == fresh[k] for k in (
                "image_id", "database_sha256", "status_sha256", "output", "blocked",
            )), message(
                en="The gate must retain actual scanner evidence, not fabricated findings.",
                fr="La barrière doit conserver la preuve réelle, pas des alertes fabriquées.",
            )
        finally:
            host.run("rm -f %s", path)
