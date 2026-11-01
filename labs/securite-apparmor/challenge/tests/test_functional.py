"""Check an enforcing, uniquely named profile and its path-specific denial."""

import json

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_profile_denies_only_the_private_read(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-securite-apparmor "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "securite-apparmor", message(fr="Conserver le label", en="Preserve the label")
    assert info["AppArmorProfile"] == "dsoxlab-securite-apparmor", message(fr="Attacher le profil dédié", en="Attach the dedicated profile")
    active = host.run("docker exec %s cat /proc/1/attr/current", cid)
    assert active.rc == 0 and active.stdout.strip() == "dsoxlab-securite-apparmor (enforce)", message(fr="Un profil en complain ne suffit pas", en="A complain profile is insufficient")
    public = host.run("docker exec %s cat /lab/public.txt", cid)
    assert public.rc == 0 and public.stdout == "public", message(fr="La lecture publique doit fonctionner", en="Public read must work")
    mode = host.run("docker exec %s stat -c %%a /lab/private.txt", cid)
    assert mode.rc == 0 and mode.stdout.strip() == "444", message(fr="Ne pas remplacer AppArmor par chmod", en="Do not substitute chmod for AppArmor")
    private = host.run("docker exec %s cat /lab/private.txt", cid)
    assert private.rc != 0 and "Permission denied" in private.stderr, message(fr="La lecture privée doit être refusée", en="Private read must be denied")
