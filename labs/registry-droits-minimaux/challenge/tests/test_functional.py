"""A real token ACL must govern transfers between two independent engines."""

from __future__ import annotations

import json
import secrets

from conftest import lab_host, lab_host_ip, message

REGISTRY = "registry-rights.lab.test:15447"
WORK = "/opt/lab-registry-rights"
IMAGE = f"{REGISTRY}/catalogue/appli"


def _require(result, en, fr):
    assert result.rc == 0, message(en=en, fr=fr)
    return result.stdout.strip()


def _login(host, directory, account, password):
    result = host.run(
        "mkdir -p %s && printf '%%s' %s | docker --config %s login %s --username %s --password-stdin",
        directory, password, directory, REGISTRY, account,
    )
    _require(result, "The synthetic account must log in over verified TLS.", "Le compte synthétique doit se connecter en TLS vérifié.")


def _status(host, path, token=None, method="GET"):
    command = (
        "curl --noproxy '*' --silent --show-error --max-time 10 --cacert %s "
        "--request %s --output /dev/null --write-out '%%{http_code}' %s"
    )
    args = [f"{WORK}/ca.crt", method, f"https://{REGISTRY}{path}"]
    if token:
        command += " --header %s"
        args.append(f"Authorization: Bearer {token}")
    result = host.run(command, *args)
    return _require(result, "The HTTPS request must complete with strict certificate checks.", "La requête HTTPS doit aboutir avec vérification stricte du certificat.")


def _token(host, credentials, scope):
    result = host.run(
        "curl --noproxy '*' --fail --silent --show-error --max-time 10 --cacert %s --user %s --get "
        "--data-urlencode %s --data-urlencode %s %s",
        f"{WORK}/ca.crt", credentials, "service=dsoxlab-registry", f"scope={scope}",
        "https://registry-rights.lab.test:15448/auth",
    )
    return json.loads(_require(result, "The scope service must issue a token.", "Le service de scopes doit émettre un jeton."))["token"]


def test_minimal_acl_controls_push_and_a_fresh_second_host_digest_pull():
    publisher, reader = lab_host("docker.lab"), lab_host("docker-client.lab")
    assert lab_host_ip("docker.lab") != lab_host_ip("docker-client.lab"), message(
        en="The reader must use a different VM.", fr="Le lecteur doit utiliser une autre VM.",
    )
    accounts = json.loads(publisher.file(f"{WORK}/credentials.json").content_string)
    tag = f"{IMAGE}:probe-{secrets.token_hex(10)}"
    nonce = secrets.token_hex(32)
    context = f"{WORK}/probe"
    pubconfig, readconfig = f"{WORK}/publisher", f"{WORK}/reader"
    identity = None
    try:
        _login(publisher, pubconfig, "publisher", accounts["publisher"])
        _require(publisher.run(
            "mkdir -p %s && cp %s %s && printf '%%s\\n' %s > %s && docker build -t %s %s",
            context, f"{WORK}/Dockerfile", f"{context}/Dockerfile", nonce,
            f"{context}/release.txt", tag, context,
        ), "Build a fresh labelled product.", "Construire un produit neuf étiqueté.")
        pushed = publisher.run("docker --config %s push %s", pubconfig, tag)
        _require(pushed, "Grant the publisher pull and push only on catalogue/appli.", "Accordez à publisher pull et push seulement sur catalogue/appli.")
        identity = _require(publisher.run("docker image inspect %s --format %s", tag, "{{.Id}}"), "Inspect the published image.", "Inspecter l'image publiée.")
        digests = json.loads(_require(publisher.run(
            "docker image inspect %s --format %s", tag, "{{json .RepoDigests}}",
        ), "Inspect the published digest.", "Inspecter le digest publié."))
        digest = next(item for item in digests if item.startswith(f"{IMAGE}@sha256:"))
        absent = reader.run("docker image inspect %s", identity)
        assert absent.rc != 0, message(
            en="The exact newly built product must not be cached on the separate reader.",
            fr="Le produit exact nouvellement construit ne doit pas être en cache sur le lecteur distinct.",
        )
        _login(reader, readconfig, "reader", accounts["reader"])
        _require(reader.run("docker --config %s pull %s", readconfig, digest),
                 "The separate reader must pull the immutable digest over TLS.", "Le lecteur distinct doit tirer le digest immuable en TLS.")
        pulled_id = _require(reader.run("docker image inspect %s --format %s", digest, "{{.Id}}"), "Inspect the reader image.", "Inspecter l'image du lecteur.")
        assert pulled_id == identity, message(en="The two engines must agree on the exact image ID.", fr="Les deux moteurs doivent avoir l'identifiant d'image exact.")
        product = reader.run(
            "docker run --rm --name dsoxlab-registry-droits-minimaux-consumer "
            "--label dsoxlab.lab=registry-droits-minimaux --network none %s", digest,
        )
        assert product.rc == 0 and product.stdout.strip() == nonce, message(
            en="The transferred product must preserve its runtime nonce without network access.",
            fr="Le produit transféré doit conserver son nonce d'exécution sans accès réseau.",
        )
        _require(reader.run("docker tag %s %s", digest, tag), "Tag the reader upload probe.", "Étiqueter la sonde d'upload du lecteur.")
        denied = reader.run("docker --config %s push %s", readconfig, tag)
        assert denied.rc != 0 and any(word in denied.stderr.lower() for word in ("denied", "unauthorized")), message(
            en="The read-only account must be unable to push even the already existing image.",
            fr="Le compte lecture seule doit être incapable de pousser même l'image existante.",
        )
        readtoken = _token(reader, f"reader:{accounts['reader']}", "repository:catalogue/appli:pull,push")
        assert _status(reader, "/v2/catalogue/appli/blobs/uploads/", readtoken, "POST") == "401", message(
            en="A requested push scope must not grant the reader an upload session.",
            fr="Un scope push demandé ne doit pas donner une session d'upload au lecteur.",
        )
        for account in ("publisher", "reader"):
            token = _token(reader, f"{account}:{accounts[account]}", "repository:other/product:pull,push")
            assert _status(reader, "/v2/other/product/blobs/uploads/", token, "POST") == "401", message(
                en="Neither account may upload to repositories outside the approved ACL.",
                fr="Aucun compte ne doit uploader hors du dépôt approuvé par l'ACL.",
            )
            assert _status(reader, "/v2/other/product/manifests/missing", token) == "401", message(
                en="Neither account may read repositories outside the approved ACL.",
                fr="Aucun compte ne doit lire hors du dépôt approuvé par l'ACL.",
            )
        assert _status(reader, "/v2/") == "401", message(en="Anonymous access must be rejected.", fr="L'accès anonyme doit être refusé.")
        bad = reader.run(
            "curl --noproxy '*' --silent --max-time 10 --cacert %s --user %s --output /dev/null "
            "--write-out '%%{http_code}' %s",
            f"{WORK}/ca.crt", f"reader:{secrets.token_hex(24)}", "https://registry-rights.lab.test:15448/auth",
        )
        assert bad.rc == 0 and bad.stdout == "401", message(en="Wrong credentials must be rejected.", fr="Les mauvais identifiants doivent être refusés.")
        wrongname = reader.run(
            "curl --noproxy '*' --silent --max-time 10 --cacert %s --resolve %s %s",
            f"{WORK}/ca.crt", f"wrong.lab.test:15447:{lab_host_ip('docker.lab')}",
            "https://wrong.lab.test:15447/v2/",
        )
        assert wrongname.rc == 60, message(en="A wrong hostname must fail certificate verification.", fr="Un mauvais nom doit échouer à la vérification du certificat.")
        for host in (publisher, reader):
            info = json.loads(_require(host.run("docker info --format %s", "{{json .RegistryConfig}}"), "Inspect effective Docker trust.", "Inspecter la confiance Docker effective."))
            entry = info.get("IndexConfigs", {}).get(REGISTRY)
            assert entry is None or entry.get("Secure"), message(en="The registry must not be insecure.", fr="Le registre ne doit pas être insecure.")
        trust = f"/etc/docker/certs.d/{REGISTRY}/ca.crt"
        _require(reader.run("mv %s %s", trust, f"{trust}.saved"), "Remove the lab CA temporarily.", "Retirer temporairement la CA du lab.")
        try:
            untrusted = reader.run("docker --config %s pull %s", readconfig, digest)
            assert untrusted.rc != 0 and "x509" in untrusted.stderr.lower(), message(
                en="Without the CA, Docker must refuse the registry, even with cached layers.",
                fr="Sans CA, Docker doit refuser le registre, même avec des couches en cache.",
            )
        finally:
            _require(reader.run("mv %s %s", f"{trust}.saved", trust), "Restore the CA.", "Restaurer la CA.")
    finally:
        for host in (reader, publisher):
            image = host.run("docker image inspect %s --format %s", tag, "{{.Id}}")
            if image.rc == 0:
                _require(host.run("docker image rm -f %s", image.stdout.strip()), "Remove the owned trial image.", "Retirer l'image d'essai possédée.")
            elif identity is not None and host.run("docker image inspect %s", identity).rc == 0:
                _require(host.run("docker image rm -f %s", identity), "Remove the owned digest image.", "Retirer l'image par digest possédée.")
        _require(publisher.run("rm -rf %s", context), "Remove the owned build context.", "Retirer le contexte de build possédé.")
