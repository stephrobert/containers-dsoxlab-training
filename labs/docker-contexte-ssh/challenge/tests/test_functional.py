"""Verify that the named Docker context uses its dedicated SSH endpoint."""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_named_context_uses_ssh_without_changing_the_default(host):
    state_file = host.file("/opt/dsoxlab-docker-contexte-ssh/state.json")
    assert state_file.exists, message(
        en="The prepared SSH context state is missing.",
        fr="L'état préparé du contexte SSH est absent.",
    )
    state = json.loads(state_file.content_string)

    def run_as_learner(*args):
        return host.run(
            shlex.join(
                ["sudo", "-n", "-u", state["learner"], "--", *args]
            )
        )

    inspected = run_as_learner("docker", "context", "inspect", "dsoxlab-maintenance")
    assert inspected.rc == 0, message(
        en="Create the named dsoxlab-maintenance context.",
        fr="Créez le contexte nommé dsoxlab-maintenance.",
    )
    context = json.loads(inspected.stdout)[0]
    endpoint = context["Endpoints"]["docker"]["Host"]
    assert endpoint == "ssh://dsoxlab-ssh-target", message(
        en=f"The context must use the prepared SSH alias, not a local socket (found {endpoint!r}).",
        fr=f"Le contexte doit utiliser l'alias SSH préparé, pas un socket local (valeur : {endpoint!r}).",
    )
    default_context = run_as_learner("docker", "context", "show")
    assert default_context.rc == 0 and default_context.stdout.strip() == state["default_context"], message(
        en="Keep the learner's original default Docker context selected.",
        fr="Conservez le contexte Docker par défaut.",
    )
    remote_info = run_as_learner(
        "docker", "--context", "dsoxlab-maintenance", "info", "--format", "{{.ID}}"
    )
    target = lab_host("docker-client.lab").run("docker info --format '{{.ID}}'")
    local = host.run("docker info --format '{{.ID}}'")
    assert target.rc == local.rc == 0 and (
        remote_info.stdout.strip() == target.stdout.strip() != local.stdout.strip()
    ), message(
        en="The context must contact the real second-VM engine, not a loopback alias to the source.",
        fr="Le contexte doit joindre le vrai moteur de la seconde VM, pas un alias loopback de la source.",
    )
    denied_command = shlex.join([
        "ssh", "-F", "/dev/null", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
        "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=5", "-i", "/opt/dsoxlab-docker-contexte-ssh/unauthorized",
        f"dsoxlab-context@{state['remote_ip']}", "docker", "info", "--format", "{{.ID}}",
    ])
    # Testinfra treats an outer SSH exit 255 as a transport failure.
    unauthorized = run_as_learner(
        "sh", "-c", denied_command
        + '; status=$?; printf "\\nssh_exit=%s\\n" "$status"; test "$status" -eq 255',
    )
    assert unauthorized.rc == 0 and "Permission denied" in unauthorized.stderr and (
        unauthorized.stdout.strip() == "ssh_exit=255"
    ), message(
        en="The reachable remote SSH service must reject the separate unauthorized identity.",
        fr="Le service SSH distant joignable doit refuser l'identité distincte non autorisée.",
    )
    assert remote_info.rc == 0 and remote_info.stdout.strip(), message(
        en=f"The SSH context cannot reach its Docker daemon: {remote_info.stderr[-500:]}",
        fr=f"Le contexte SSH ne joint pas son démon Docker : {remote_info.stderr[-500:]}",
    )
