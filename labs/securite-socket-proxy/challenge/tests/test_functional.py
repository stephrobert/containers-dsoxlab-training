"""Verify that the loopback proxy allows only the required read endpoints."""

from __future__ import annotations

import shlex

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def _status(host, method, path):
    result = host.run(
        shlex.join(
            [
                "curl",
                "--noproxy",
                "*",
                "--silent",
                "--show-error",
                "--output",
                "/dev/null",
                "--write-out",
                "%{http_code}",
                "--request",
                method,
                f"http://127.0.0.1:2376{path}",
            ]
        )
    )
    assert result.rc == 0, message(
        en=f"The loopback proxy request failed: {result.stderr[-500:]}",
        fr=f"La requête au proxy local a échoué : {result.stderr[-500:]}",
    )
    return result.stdout.strip()


def test_proxy_allows_only_health_and_version_reads(host):
    service = host.run("systemctl is-active dsoxlab-securite-socket-proxy.service")
    assert service.rc == 0 and service.stdout.strip() == "active", message(
        en="Start the dedicated loopback Docker API proxy.",
        fr="Démarrez le proxy dédié de l'API Docker sur la boucle locale.",
    )
    assert _status(host, "GET", "/_ping") == "200", message(
        en="Allow the Docker health endpoint GET /_ping.",
        fr="Autorisez le point de santé Docker GET /_ping.",
    )
    assert _status(host, "GET", "/version") == "200", message(
        en="Allow the Docker version endpoint GET /version.",
        fr="Autorisez le point de version Docker GET /version.",
    )
    assert _status(host, "GET", "/containers/json") == "403", message(
        en="Deny unrelated Docker API reads.",
        fr="Refusez les lectures d'autres points de l'API Docker.",
    )
    assert _status(host, "HEAD", "/version") == "403", message(
        en="Allow only GET requests to the two required read endpoints.",
        fr="Autorisez uniquement les requêtes GET vers les deux points de lecture requis.",
    )
    assert _status(host, "POST", "/containers/create") == "403", message(
        en="Deny Docker API mutations.",
        fr="Refusez les modifications de l'API Docker.",
    )
