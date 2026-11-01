"""Finite 1 MiB write in a verified 16 MiB sandbox, never on a host partition."""

import json
import uuid

import pytest

from conftest import lab_host, message


@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_space_reclaimed_without_destroying_retained_data(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=dsoxlab-troubleshoot-disque-plein "
        "--filter label=com.docker.compose.service=worker"
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    config = info["HostConfig"]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "troubleshoot-disque-plein", message(fr="Conserver le label", en="Preserve the label")
    original = host.run("cat /opt/dsoxlab-troubleshoot-disque-plein/.starter-id")
    assert original.rc == 0 and info["Id"] == original.stdout.strip(), message(fr="Conserver le conteneur initial et ses données", en="Keep the initial container and its data")
    assert "/sandbox" in config["Tmpfs"] and config["Memory"] == 67108864 and config["MemorySwap"] == 67108864, message(fr="Conserver le sandbox tmpfs et sa limite mémoire", en="Preserve the tmpfs sandbox and memory cap")
    filesystem = host.run("docker exec %s sh -c 'stat -f -c %%T /sandbox; df -Pk /sandbox'", cid)
    assert filesystem.rc == 0 and filesystem.stdout.splitlines()[0] == "tmpfs", message(fr="Ne jamais écrire dans une partition hôte", en="Never write into a host partition")
    assert int(filesystem.stdout.splitlines()[-1].split()[1]) == 16384, message(fr="Conserver le plafond strict de 16 Mio", en="Preserve the strict 16 MiB cap")
    removed = host.run("docker exec %s sh -c 'test ! -e /sandbox/fill.bin'", cid)
    assert removed.rc == 0, message(fr="Retirer le remplissage jetable", en="Remove disposable filler")
    keep = host.run("docker exec %s cat /sandbox/keep.txt", cid)
    assert keep.rc == 0 and keep.stdout == "keep-this-receipt\n", message(fr="Préserver les données utiles", en="Preserve useful data")
    name = "/sandbox/dsoxlab-check-" + uuid.uuid4().hex
    try:
        write = host.run("timeout 5 docker exec %s dd if=/dev/zero of=%s bs=1M count=1", cid, name)
        assert write.rc == 0, message(fr="Une vraie écriture de 1 Mio doit réussir", en="A real 1 MiB write must succeed")
        size = host.run("docker exec %s stat -c %%s %s", cid, name)
        assert size.rc == 0 and size.stdout.strip() == "1048576", message(fr="Vérifier les octets réellement écrits", en="Verify actual bytes written")
    finally:
        host.run("docker exec %s rm -f %s", cid, name)
