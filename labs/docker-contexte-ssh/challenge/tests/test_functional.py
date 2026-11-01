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
        "docker", "--context", "dsoxlab-maintenance", "info", "--format", "{{.Name}}"
    )
    assert remote_info.rc == 0 and remote_info.stdout.strip(), message(
        en=f"The SSH context cannot reach its Docker daemon: {remote_info.stderr[-500:]}",
        fr=f"Le contexte SSH ne joint pas son démon Docker : {remote_info.stderr[-500:]}",
    )
