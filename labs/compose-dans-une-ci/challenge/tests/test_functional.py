"""Execute the learner's local CI against success, failure and changed source."""

from __future__ import annotations

import json
import shlex
import uuid

import pytest

from conftest import lab_host, message

ROOT = "/opt/lab-compose-ci"


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _run(host, *, fail=False, dirty=False):
    token = uuid.uuid4().hex[:12]
    project = f"dsoxlab-ci-{token}"
    trial = f"{ROOT}/trials/{token}"
    value = f"release-{token}"
    prepared = host.run(
        "mkdir -p %s/source %s/artifacts && cp %s/source/* %s/source/ && printf '%%s' %s > %s/source/value.txt",
        trial, trial, ROOT, trial, value, trial,
    )
    assert prepared.rc == 0, message(
        en="Cannot prepare the isolated CI trial.", fr="Impossible de préparer l'essai CI isolé.",
    )
    try:
        committed = host.run(
            "set -eu; cp %s/source/.dockerignore %s/source/; "
            "git -C %s/source init -q; git -C %s/source add .; "
            "git -C %s/source -c user.name=DSOxLab -c user.email=fixture@invalid commit -q "
            "-m 'Isolated CI trial' -m 'Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>'; "
            "git -C %s/source rev-parse HEAD",
            ROOT, trial, trial, trial, trial, trial,
        )
        assert committed.rc == 0, message(
            en="Commit the fresh source in this isolated CI repository.",
            fr="Commitez la source nouvelle dans le dépôt CI isolé.",
        )
        source_commit = committed.stdout.strip()
        if dirty:
            changed = host.run("printf '%%s' %s > %s/source/value.txt", "uncommitted-" + token, trial)
            assert changed.rc == 0, message(
                en="Inject an uncommitted source change.",
                fr="Injectez une modification de source non commitée.",
            )
        command = shlex.join([
            "env", f"PROJECT={project}", f"SOURCE_DIR={trial}/source",
            f"ARTIFACT_DIR={trial}/artifacts", f"EXPECTED_VALUE={value}",
            f"TEST_FAIL={int(fail)}", "timeout", "120", f"{ROOT}/ci.sh",
        ])
        result = host.run(command)
        report = host.run("cat %s/artifacts/result.json", trial)
        containers = host.run("docker ps -aq --filter %s", f"label=com.docker.compose.project={project}")
        networks = host.run("docker network ls -q --filter %s", f"label=com.docker.compose.project={project}")
        assert containers.rc == networks.rc == 0 and not containers.stdout.strip() and not networks.stdout.strip(), message(
            en="The CI must remove its containers and network on success AND failure.",
            fr="La CI doit retirer ses conteneurs et son réseau en succès ET en échec.",
        )
        publication = host.run("cat %s/artifacts/image.json", trial)
        archive = host.run("test -f %s/artifacts/release.tar", trial)
        if dirty:
            assert result.rc not in (0, 124, 127) and "uncommitted" in (result.stdout + result.stderr).lower() and (
                publication.rc != 0 and archive.rc != 0
            ), message(
                en="Explicitly reject uncommitted source without publishing an accepted artifact.",
                fr="Refusez explicitement la source non commitée sans publier d'artefact accepté.",
            )
            return result
        assert report.rc == 0, message(
            en="Run the supplied test container and retain artifacts/result.json.",
            fr="Exécutez le conteneur de test fourni et conservez artifacts/result.json.",
        )
        data = json.loads(report.stdout)
        assert data.get("observed") == value and data.get("expected") == value, message(
            en="Build and query this trial's changed source, not a cached previous release.",
            fr="Construisez et interrogez la source modifiée de cet essai, pas une ancienne livraison en cache.",
        )
        assert data.get("passed") is (not fail), message(
            en="Preserve the actual test verdict, including TEST_FAIL=1.",
            fr="Conservez le verdict réel du test, y compris TEST_FAIL=1.",
        )
        if fail:
            assert publication.rc != 0 and archive.rc != 0, message(
                en="A failing application test must never publish an accepted image archive.",
                fr="Un test applicatif échoué ne publie jamais d'archive d'image acceptée.",
            )
        else:
            assert publication.rc == archive.rc == 0, message(
                en="Publish the successfully tested image as release.tar with image.json provenance.",
                fr="Publiez l'image testée avec succès dans release.tar avec sa provenance image.json.",
            )
            published = json.loads(publication.stdout)
            loaded = host.run("docker image load -i %s/artifacts/release.tar", trial)
            image = host.run("docker image inspect %s", project + "-api")
            digest = host.run("sha256sum %s/artifacts/release.tar", trial)
            assert loaded.rc == image.rc == digest.rc == 0, message(
                en="Reload and inspect the real published archive.",
                fr="Rechargez et inspectez l'archive réellement publiée.",
            )
            actual = json.loads(image.stdout)[0]
            assert published["source_commit"] == source_commit == actual["Config"]["Labels"]["org.opencontainers.image.revision"] and (
                published["image_id"] == actual["Id"] and published["sha256"] == digest.stdout.split()[0]
            ), message(
                en="Tie the accepted archive, loaded image identity and OCI revision to the actual committed fresh source.",
                fr="Reliez archive acceptée, identité de l'image chargée et révision OCI à la source nouvelle réellement commitée.",
            )
            git_absent = host.run(
                "docker run --rm --network none --entrypoint sh %s -c 'test ! -d /app/.git'",
                actual["Id"],
            )
            assert git_absent.rc == 0, message(
                en="Do not copy Git repository internals into the runtime image.",
                fr="Ne copiez pas les données internes Git dans l'image runtime.",
            )
        return result
    finally:
        host.run(
            "docker ps -aq --filter %s | xargs -r docker rm -f; "
            "docker network ls -q --filter %s | xargs -r docker network rm; "
            "docker image ls -q --filter reference=%s | xargs -r docker image rm -f; rm -rf %s",
            f"label=com.docker.compose.project={project}",
            f"label=com.docker.compose.project={project}", f"{project}-api", trial,
        )


def test_success_builds_waits_tests_and_cleans(host):
    result = _run(host)
    assert result.rc == 0, message(
        en="A successful test must yield CI exit code zero.",
        fr="Un test réussi doit donner un code de sortie CI nul.",
    )


def test_failed_test_fails_ci_and_still_cleans(host):
    result = _run(host, fail=True)
    assert result.rc not in (0, 124, 127), message(
        en="Return the failing test's exit status, not success, timeout or a missing command.",
        fr="Retournez le statut du test échoué, pas un succès, un délai expiré ou une commande absente.",
    )


def test_fresh_source_is_rebuilt_on_each_invocation(host):
    for _ in range(2):
        result = _run(host)
        assert result.rc == 0, message(
            en="Repeated CI runs must rebuild changed source and remain independent.",
            fr="Les exécutions répétées doivent reconstruire la source modifiée et rester indépendantes.",
        )


def test_uncommitted_source_is_refused_after_a_successful_release(host):
    assert _run(host).rc == 0, message(
        en="First prove that a committed source produces an accepted release.",
        fr="Prouvez d'abord qu'une source commitée produit une livraison acceptée.",
    )
    _run(host, dirty=True)
