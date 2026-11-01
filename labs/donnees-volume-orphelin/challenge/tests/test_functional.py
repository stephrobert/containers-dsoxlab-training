"""Recover retained data and remove only the lab's expendable orphan."""

import json

import pytest

from conftest import lab_host, message

PROJECT = "dsoxlab-donnees-volume-orphelin"
VOLUME = PROJECT + "-data"

@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_retained_volume_reconnected_without_data_loss(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=%s "
        "--filter label=com.docker.compose.service=worker", PROJECT,
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "donnees-volume-orphelin", message(fr="Conserver le label", en="Preserve the label")
    mounts = [mount for mount in info["Mounts"] if mount["Destination"] == "/data"]
    assert len(mounts) == 1 and mounts[0]["Type"] == "volume" and mounts[0]["Name"] == VOLUME and not mounts[0]["RW"], message(fr="Reconnecter le volume original en lecture seule", en="Reconnect the original volume read-only")
    volume = host.run("docker volume inspect %s", VOLUME)
    assert volume.rc == 0, message(fr="Conserver le volume original", en="Retain the original volume")
    volume_info = json.loads(volume.stdout)[0]
    labels = volume_info["Labels"]
    assert labels.get("dsoxlab.lab") == "donnees-volume-orphelin" and labels.get("com.docker.compose.project") == PROJECT, message(fr="Conserver les deux labels de propriété", en="Preserve both ownership labels")
    created = host.run("cat /opt/dsoxlab-donnees-volume-orphelin/.volume-created")
    assert created.rc == 0 and created.stdout.strip() == volume_info["CreatedAt"], message(fr="Ne pas recréer le volume original", en="Do not recreate the original volume")
    expected = host.run("cat /opt/dsoxlab-donnees-volume-orphelin/expected.txt")
    actual = host.run("docker exec %s cat /data/receipt.txt", cid)
    assert expected.rc == 0 and actual.rc == 0 and actual.stdout == expected.stdout and actual.stdout.startswith("receipt="), message(fr="Les données originales doivent être intactes", en="Original data must remain intact")
    stale = host.run("docker volume inspect %s-stale", PROJECT)
    assert stale.rc != 0, message(fr="Retirer uniquement l'orphelin périmé du lab", en="Remove only the lab's stale orphan")
