"""A single scored proof: declared and effective capabilities must agree."""

import json

import pytest

from conftest import lab_host, message

PROJECT = "dsoxlab-securite-capabilities"

@pytest.fixture
def host():
    return lab_host("docker.lab")


def test_only_bind_service_remains(host):
    found = host.run(
        "docker ps -q --filter label=com.docker.compose.project=%s "
        "--filter label=com.docker.compose.service=worker", PROJECT,
    )
    ids = found.stdout.split()
    assert found.rc == 0 and len(ids) == 1, message(fr="Un service actif requis", en="One running service required")
    cid = ids[0]
    info = json.loads(host.run("docker inspect %s", cid).stdout)[0]
    config = info["HostConfig"]
    assert info["Config"]["Labels"].get("dsoxlab.lab") == "securite-capabilities", message(fr="Conserver le label", en="Preserve the label")
    # Docker 29 NORMALISE les capabilities avec leur prefixe `CAP_` :
    # `--cap-add NET_BIND_SERVICE` ressort en `[CAP_NET_BIND_SERVICE]`.
    # On compare donc des noms canoniques, ce qui accepte les deux
    # ecritures cote apprenant sans rien relacher. `ALL` reste `ALL` :
    # ce n'est pas une capability, c'est le mot qui les designe toutes.
    def canonique(noms):
        return sorted(
            n if n == "ALL" else "CAP_" + n.removeprefix("CAP_")
            for n in (noms or [])
        )

    assert canonique(config["CapDrop"]) == ["ALL"] and canonique(config["CapAdd"]) == ["CAP_NET_BIND_SERVICE"], message(fr="Retirer ALL et ne garder que NET_BIND_SERVICE", en="Drop ALL and retain only NET_BIND_SERVICE")
    status = host.run("docker exec %s cat /proc/1/status", cid)
    effective = next(line.split()[1] for line in status.stdout.splitlines() if line.startswith("CapEff:"))
    assert status.rc == 0 and int(effective, 16) == 1 << 10, message(fr="Le masque effectif doit valoir 0x400", en="Effective mask must be 0x400")
    denied = host.run("docker exec %s chown 123:123 /proof", cid)
    assert denied.rc != 0, message(fr="CHOWN doit réellement être refusé", en="CHOWN must actually be denied")
    owner = host.run("docker exec %s stat -c %%u /proof", cid)
    assert owner.rc == 0 and owner.stdout.strip() == "0", message(fr="La sonde ne doit pas changer le propriétaire", en="Probe must not change the owner")
