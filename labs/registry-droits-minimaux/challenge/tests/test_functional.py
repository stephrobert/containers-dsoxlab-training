"""Une livraison rétablie, sans que la frontière du registre s'élargisse.

Pourquoi deux contrôles là où il n'y en avait qu'un
--------------------------------------------------

Le fichier précédent portait **un** `def test_` et **quatorze** assertions
enchaînées, sur deux VM. C'est le plus chargé du catalogue, et son contenu est
bon : il éprouve la livraison, le refus de publication du lecteur, la frontière
du registre et la vérification TLS, chacun par un geste réel.

IL PORTE MÊME UNE CORRECTION EXEMPLAIRE, conservée telle quelle. Son commentaire
documente une mesure du 2026-11-02 : repousser l'image qu'on vient de tirer sort
en 0 **sans rien écrire**, le client voyant chaque couche et le manifeste déjà
présents, et le journal du registre ne portant alors aucun PUT. Le refus attendu
n'avait donc aucune occasion de se produire, et le contrôle mesurait une
optimisation du client au lieu d'un droit. Une image dérivée en une ligne rend le
manifeste inédit, le téléversement nécessaire, et le refus observable. C'est
exactement la rigueur que ce découpage cherche ailleurs.

LE DÉFAUT ÉTAIT DONC LA SEULE FORME : la première assertion qui tombait masquait
les treize suivantes, sur un lab dont le cycle complet dure plus d'une minute et
touche deux machines.

UNE SEULE FAMILLE D'EXIGENCES ÉCHOUE AU DÉPART, et c'est structurel. Le scénario
le dit : « rétablissez le chemin de livraison **sans élargir sa frontière** ».
Au départ, aucun compte ne peut distribuer : la livraison échoue. Mais le lecteur
ne peut déjà pas publier, l'accès anonyme est déjà refusé, et le TLS est déjà
vérifié. Ces trois familles sont des **préservations**, vraies avant tout
travail, et un contrôle qui passe avant tout travail accorde des points pour
rien.

Elles vivent donc dans un garde-fou commun, appelé par les deux contrôles, dont
le message nomme l'élargissement constaté. C'est la neuvième fois que ce cas se
présente dans ce catalogue, et la règle est établie : ce qui est vrai avant tout
travail ne peut pas être un contrôle, et appartient à celui dont il conditionne
le sens.

Les deux contrôles découpent donc la livraison elle-même :

1. l'éditeur **publie** sur son dépôt, et le registre lui rend un digest ;
2. le lecteur distinct **tire ce digest**, le produit répond, et ce même lecteur
   **ne peut pas publier**.

Le second refait sa publication plutôt que de compter sur le premier : un
contrôle qui suppose qu'un autre a tourné mentirait dès qu'on le joue seul. C'est
un cycle de plus sur deux VM, et c'est le prix de l'indépendance.
"""

from __future__ import annotations

import json
import secrets

import pytest

from conftest import lab_host, lab_host_ip, message

REGISTRY = "registry-rights.lab.test:15447"
AUTH = "https://registry-rights.lab.test:15448/auth"
WORK = "/opt/lab-registry-rights"
IMAGE = f"{REGISTRY}/catalogue/appli"
LAB = "registry-droits-minimaux"
# Le fichier vit sur la machine du lab, jamais sur un poste partagé.
SONDE_CONTEXTE = f"/tmp/dsoxlab-{LAB}-sonde"  # noqa: S108


def _require(resultat, en, fr):
    assert resultat.rc == 0, message(en=en, fr=fr)
    return resultat.stdout.strip()


def _login(host, repertoire, compte, mot_de_passe):
    resultat = host.run(
        "mkdir -p %s && printf '%%s' %s | docker --config %s login %s --username %s --password-stdin",
        repertoire, mot_de_passe, repertoire, REGISTRY, compte,
    )
    _require(
        resultat,
        "The synthetic account must log in over verified TLS.",
        "Le compte synthétique doit se connecter en TLS vérifié.",
    )


def _status(host, chemin, jeton=None, methode="GET"):
    commande = (
        "curl --noproxy '*' --silent --show-error --max-time 10 --cacert %s "
        "--request %s --output /dev/null --write-out '%%{http_code}' %s"
    )
    args = [f"{WORK}/ca.crt", methode, f"https://{REGISTRY}{chemin}"]
    if jeton:
        commande += " --header %s"
        args.append(f"Authorization: Bearer {jeton}")
    return _require(
        host.run(commande, *args),
        "The HTTPS request must complete with strict certificate checks.",
        "La requête HTTPS doit aboutir avec vérification stricte du certificat.",
    )


def _token(host, identifiants, scope):
    resultat = host.run(
        "curl --noproxy '*' --fail --silent --show-error --max-time 10 --cacert %s "
        "--user %s --get --data-urlencode %s --data-urlencode %s %s",
        f"{WORK}/ca.crt", identifiants, "service=dsoxlab-registry", f"scope={scope}", AUTH,
    )
    return json.loads(_require(
        resultat,
        "The scope service must issue a token.",
        "Le service de scopes doit émettre un jeton.",
    ))["token"]


@pytest.fixture
def machines():
    """Les deux moteurs, et la preuve qu'ils sont bien distincts.

    Garde-fou de mesure : tout ce lab repose sur le fait que le lecteur vit
    ailleurs. Deux noms pour la même machine rendraient chaque comparaison
    vraie sans rien prouver.
    """
    editeur, lecteur = lab_host("docker.lab"), lab_host("docker-client.lab")
    assert lab_host_ip("docker.lab") != lab_host_ip("docker-client.lab"), message(
        en="The reader must use a different VM. Not your fault: the comparison "
           "cannot be made, report it.",
        fr="Le lecteur doit utiliser une autre VM. Ce n'est pas votre faute : la "
           "comparaison ne peut pas être faite, signalez-le.",
    )
    return editeur, lecteur


@pytest.fixture
def comptes(machines):
    editeur, _lecteur = machines
    return json.loads(editeur.file(f"{WORK}/credentials.json").content_string)


def _frontiere_intacte(machines, comptes) -> None:
    """La frontière du registre n'a pas été élargie.

    GARDE-FOU ET NON EXIGENCE : ces trois familles sont vraies avant tout
    travail. Le scénario les énonce comme la contrainte de la mission, « sans
    élargir sa frontière », et les franchir est une faute qui doit se dire.

    Donner les droits d'administration aux deux comptes rétablirait la livraison
    et ferait du serveur de déploiement un éditeur : c'est le contresens que ce
    garde-fou refuse.
    """
    _editeur, lecteur = machines

    # UN SCOPE DEMANDÉ N EST PAS UN DROIT ACCORDÉ. Le lecteur peut réclamer un
    # jeton de push ; le registre doit refuser la session d'upload.
    jeton = _token(lecteur, f"reader:{comptes['reader']}",
                   "repository:catalogue/appli:pull,push")
    assert _status(lecteur, "/v2/catalogue/appli/blobs/uploads/", jeton, "POST") == "401", message(
        en="A requested push scope granted the reader an upload session. Asking "
           "for a scope is not being granted it: the ACL decides, not the client.",
        fr="Un scope push demandé a donné une session d'upload au lecteur. "
           "Demander un scope n'est pas l'obtenir : c'est l'ACL qui décide, pas "
           "le client.",
    )

    # AUCUN DES DEUX COMPTES HORS DU DÉPÔT APPROUVÉ, ni en écriture ni en
    # lecture. L'éditeur non plus : son droit porte sur un dépôt, pas sur le
    # registre.
    for compte in ("publisher", "reader"):
        jeton = _token(lecteur, f"{compte}:{comptes[compte]}",
                       "repository:other/product:pull,push")
        assert _status(lecteur, "/v2/other/product/blobs/uploads/", jeton, "POST") == "401", message(
            en=f"The {compte} account may upload outside the approved repository. "
               "A minimal right names its repository.",
            fr=f"Le compte {compte} peut téléverser hors du dépôt approuvé. Un "
               "droit minimal nomme son dépôt.",
        )
        assert _status(lecteur, "/v2/other/product/manifests/missing", jeton) == "401", message(
            en=f"The {compte} account may read outside the approved repository.",
            fr=f"Le compte {compte} peut lire hors du dépôt approuvé.",
        )

    assert _status(lecteur, "/v2/") == "401", message(
        en="Anonymous access to the registry is accepted. Credentials that are "
           "not asked for are not credentials.",
        fr="L'accès anonyme au registre est accepté. Des identifiants qu'on ne "
           "demande pas n'en sont pas.",
    )

    faux = lecteur.run(
        "curl --noproxy '*' --silent --max-time 10 --cacert %s --user %s "
        "--output /dev/null --write-out '%%{http_code}' %s",
        f"{WORK}/ca.crt", f"reader:{secrets.token_hex(24)}", AUTH,
    )
    assert faux.rc == 0 and faux.stdout == "401", message(
        en=f"Wrong credentials got {faux.stdout!r} instead of 401: the scope "
           "service authenticates nobody.",
        fr=f"De mauvais identifiants ont obtenu {faux.stdout!r} au lieu de 401 : "
           "le service de scopes n'authentifie personne.",
    )


def _tls_verifie(machines) -> None:
    """Le TLS est vérifié, et pas seulement présent.

    Garde-fou, vrai au départ lui aussi. Trois choses distinctes : un mauvais
    nom doit échouer sur le certificat, aucun moteur ne doit tenir le registre
    pour `insecure`, et sans la CA le tirage doit être refusé même avec des
    couches en cache.
    """
    editeur, lecteur = machines

    mauvais_nom = lecteur.run(
        "curl --noproxy '*' --silent --max-time 10 --cacert %s --resolve %s %s",
        f"{WORK}/ca.crt", f"wrong.lab.test:15447:{lab_host_ip('docker.lab')}",
        "https://wrong.lab.test:15447/v2/",
    )
    assert mauvais_nom.rc == 60, message(
        en=f"A wrong hostname returned {mauvais_nom.rc} instead of curl's 60: the "
           "certificate is not checked against the name requested.",
        fr=f"Un mauvais nom a rendu {mauvais_nom.rc} au lieu du 60 de curl : le "
           "certificat n'est pas vérifié contre le nom demandé.",
    )

    for machine in (editeur, lecteur):
        info = json.loads(_require(
            machine.run("docker info --format %s", "{{json .RegistryConfig}}"),
            "Inspect effective Docker trust.",
            "Inspecter la confiance Docker effective.",
        ))
        entree = info.get("IndexConfigs", {}).get(REGISTRY)
        assert entree is None or entree.get("Secure"), message(
            en="An engine treats the registry as insecure. Trusting a CA is the "
               "way; disabling verification is not.",
            fr="Un moteur tient le registre pour insecure. Faire confiance à une "
               "CA est la voie ; désactiver la vérification n'en est pas une.",
        )


def test_l_editeur_publie_sur_son_depot(machines, comptes):
    """La première moitié de la livraison, et la seule qui échoue au départ.

    Un produit neuf est construit, étiqueté sur le dépôt approuvé, et poussé. Le
    registre doit rendre un digest : c'est lui que le lecteur tirera, et c'est le
    droit de l'éditeur sur CE dépôt qui le permet.
    """
    editeur, _lecteur = machines
    _frontiere_intacte(machines, comptes)
    _tls_verifie(machines)

    etiquette = f"{IMAGE}:probe-{secrets.token_hex(10)}"
    nonce = secrets.token_hex(32)
    contexte = f"{WORK}/probe"
    config = f"{WORK}/publisher"
    try:
        _login(editeur, config, "publisher", comptes["publisher"])
        _require(editeur.run(
            "mkdir -p %s && cp %s %s && printf '%%s\\n' %s > %s && docker build -t %s %s",
            contexte, f"{WORK}/Dockerfile", f"{contexte}/Dockerfile", nonce,
            f"{contexte}/release.txt", etiquette, contexte,
        ), "Build a fresh labelled product.", "Construire un produit neuf étiqueté.")

        pousse = editeur.run("docker --config %s push %s", config, etiquette)
        assert pousse.rc == 0, message(
            en=f"The publisher cannot push to its own repository: "
               f"{pousse.stderr.strip()[-300:]} Grant it pull and push on "
               "catalogue/appli, and nothing wider.",
            fr=f"L'éditeur ne peut pas pousser sur son propre dépôt : "
               f"{pousse.stderr.strip()[-300:]} Accordez-lui pull et push sur "
               "catalogue/appli, et rien de plus large.",
        )

        digests = json.loads(_require(editeur.run(
            "docker image inspect %s --format %s", etiquette, "{{json .RepoDigests}}",
        ), "Inspect the published digest.", "Inspecter le digest publié."))
        assert any(d.startswith(f"{IMAGE}@sha256:") for d in digests), message(
            en=f"The registry returned no digest for {IMAGE}: {digests}. Without "
               "it, nothing immutable can be pulled.",
            fr=f"Le registre n'a rendu aucun digest pour {IMAGE} : {digests}. "
               "Sans lui, rien d'immuable ne peut être tiré.",
        )
    finally:
        image = editeur.run("docker image inspect %s --format %s", etiquette, "{{.Id}}")
        if image.rc == 0:
            editeur.run("docker image rm -f %s", image.stdout.strip())
        editeur.run("rm -rf %s", contexte)


def test_le_lecteur_distinct_tire_le_digest_et_ne_peut_pas_publier(machines, comptes):
    """La seconde moitié, et les deux faces du titre du lab.

    Le lecteur tire par digest depuis l'autre VM, le produit répond son nonce
    sans accès réseau, et ce même lecteur ne peut pas publier un contenu inédit.
    « Des identifiants ne sont pas des permissions » : il a les premiers, pas les
    secondes.

    L'étape refait sa publication plutôt que de compter sur le contrôle
    précédent : un contrôle qui suppose qu'un autre a tourné mentirait dès qu'on
    le joue seul.
    """
    editeur, lecteur = machines
    _frontiere_intacte(machines, comptes)

    etiquette = f"{IMAGE}:probe-{secrets.token_hex(10)}"
    nonce = secrets.token_hex(32)
    contexte = f"{WORK}/probe"
    pubconfig, readconfig = f"{WORK}/publisher", f"{WORK}/reader"
    sonde = f"{IMAGE}:sonde-lecteur"
    identite = None
    try:
        _login(editeur, pubconfig, "publisher", comptes["publisher"])
        _require(editeur.run(
            "mkdir -p %s && cp %s %s && printf '%%s\\n' %s > %s && docker build -t %s %s",
            contexte, f"{WORK}/Dockerfile", f"{contexte}/Dockerfile", nonce,
            f"{contexte}/release.txt", etiquette, contexte,
        ), "Build a fresh labelled product.", "Construire un produit neuf étiqueté.")
        _require(editeur.run("docker --config %s push %s", pubconfig, etiquette),
                 "The publisher must be able to push first.",
                 "L'éditeur doit d'abord pouvoir pousser.")
        identite = _require(
            editeur.run("docker image inspect %s --format %s", etiquette, "{{.Id}}"),
            "Inspect the published image.", "Inspecter l'image publiée.",
        )
        digests = json.loads(_require(editeur.run(
            "docker image inspect %s --format %s", etiquette, "{{json .RepoDigests}}",
        ), "Inspect the published digest.", "Inspecter le digest publié."))
        digest = next(d for d in digests if d.startswith(f"{IMAGE}@sha256:"))

        # LE PRODUIT NE DOIT PAS ÊTRE DÉJÀ LÀ, sans quoi le tirage ne prouverait
        # rien : un cache local rendrait la même image sans toucher au registre.
        absent = lecteur.run("docker image inspect %s", identite)
        assert absent.rc != 0, message(
            en="The newly built product is already cached on the reader, so "
               "pulling it would prove nothing. Not your fault, report it.",
            fr="Le produit neuf est déjà en cache sur le lecteur, donc le tirer "
               "ne prouverait rien. Ce n'est pas votre faute, signalez-le.",
        )

        _login(lecteur, readconfig, "reader", comptes["reader"])
        tire = lecteur.run("docker --config %s pull %s", readconfig, digest)
        assert tire.rc == 0, message(
            en=f"The separate reader cannot pull the immutable digest: "
               f"{tire.stderr.strip()[-300:]} Grant it pull on catalogue/appli, "
               "and nothing more.",
            fr=f"Le lecteur distinct ne peut pas tirer le digest immuable : "
               f"{tire.stderr.strip()[-300:]} Accordez-lui pull sur "
               "catalogue/appli, et rien de plus.",
        )
        tiree = _require(
            lecteur.run("docker image inspect %s --format %s", digest, "{{.Id}}"),
            "Inspect the reader image.", "Inspecter l'image du lecteur.",
        )
        assert tiree == identite, message(
            en="The two engines disagree on the image ID: what arrived is not what "
               "was published, and a digest is supposed to forbid that.",
            fr="Les deux moteurs ne s'accordent pas sur l'identifiant d'image : ce "
               "qui est arrivé n'est pas ce qui a été publié, et un digest est "
               "censé l'interdire.",
        )

        produit = lecteur.run(
            "docker run --rm --name dsoxlab-%s-consumer --label dsoxlab.lab=%s "
            "--network none %s", LAB, LAB, digest,
        )
        assert produit.rc == 0 and produit.stdout.strip() == nonce, message(
            en="The transferred product did not return its runtime nonce without "
               "network access: the delivery arrived altered.",
            fr="Le produit transféré n'a pas rendu son nonce d'exécution sans "
               "accès réseau : la livraison est arrivée altérée.",
        )

        # LA SONDE POUSSE UN CONTENU INÉDIT, et c'est tout l'enjeu.
        #
        # Mesuré le 2026-11-02 sur Docker 29.9.2 : repousser l'image qu'on vient
        # de tirer sort en 0 SANS RIEN ÉCRIRE, le client voyant chaque couche et
        # le manifeste déjà présents, et le journal du registre ne portant alors
        # aucun PUT, POST ni PATCH. Le refus attendu n'avait aucune occasion de se
        # produire : on mesurait une optimisation du client, pas un droit.
        #
        # Une image dérivée en une ligne suffit à rendre le manifeste inédit : sa
        # couche de configuration doit être téléversée, donc le droit est demandé,
        # donc l'ACL peut le refuser. Mesuré : `insufficient_scope`, et un
        # `POST /v2/catalogue/appli/blobs/uploads/` en 401.
        _require(lecteur.run(
            "mkdir -p %s && printf 'FROM %s\\nLABEL dsoxlab.lab=\"%s\"\\n' > %s "
            "&& docker build -t %s %s",
            SONDE_CONTEXTE, digest, LAB, f"{SONDE_CONTEXTE}/Dockerfile", sonde,
            SONDE_CONTEXTE,
        ), "Build the reader inedit upload probe.",
           "Construire la sonde d'upload inédite du lecteur.")

        refuse = lecteur.run("docker --config %s push %s", readconfig, sonde)
        assert refuse.rc != 0, message(
            en="The read-only account pushed content the registry had never seen. "
               "Its credentials work, and that is precisely not a permission.",
            fr="Le compte en lecture seule a poussé un contenu inédit. Ses "
               "identifiants fonctionnent, et c'est précisément ce qui n'est pas "
               "une permission.",
        )
        trace = refuse.stderr.lower()
        assert any(mot in trace for mot in ("denied", "unauthorized", "insufficient_scope")), message(
            en=f"The push failed, but not on a refusal of rights: "
               f"{refuse.stderr.strip()[-300:]} A network error or a full disk "
               "would fail the same way while proving nothing about the ACL.",
            fr=f"Le push a échoué, mais pas sur un refus de droits : "
               f"{refuse.stderr.strip()[-300:]} Une erreur réseau ou un disque "
               "plein échoueraient de la même façon sans rien prouver de l'ACL.",
        )

        # SANS LA CA, LE TIRAGE DOIT ÊTRE REFUSÉ, même avec les couches en cache.
        # Ce passage est ici et non dans le garde-fou parce qu'il a besoin d'un
        # digest réellement publié, et qu'il déplace un fichier de confiance : il
        # le remet en place dans tous les cas.
        confiance = f"/etc/docker/certs.d/{REGISTRY}/ca.crt"
        _require(lecteur.run("mv %s %s", confiance, f"{confiance}.saved"),
                 "Remove the lab CA temporarily.",
                 "Retirer temporairement la CA du lab.")
        try:
            sans_ca = lecteur.run("docker --config %s pull %s", readconfig, digest)
            assert sans_ca.rc != 0 and "x509" in sans_ca.stderr.lower(), message(
                en=f"Without the CA, the registry was still accepted: "
                   f"{sans_ca.stderr.strip()[-200:]} Trust must come from the "
                   "certificate authority, not from cached layers.",
                fr=f"Sans la CA, le registre a quand même été accepté : "
                   f"{sans_ca.stderr.strip()[-200:]} La confiance doit venir de "
                   "l'autorité de certification, pas des couches en cache.",
            )
        finally:
            _require(lecteur.run("mv %s %s", f"{confiance}.saved", confiance),
                     "Restore the CA.", "Restaurer la CA.")
    finally:
        for machine in (lecteur, editeur):
            image = machine.run("docker image inspect %s --format %s", etiquette, "{{.Id}}")
            if image.rc == 0:
                machine.run("docker image rm -f %s", image.stdout.strip())
            elif identite is not None and machine.run("docker image inspect %s", identite).rc == 0:
                machine.run("docker image rm -f %s", identite)
        if lecteur.run("docker image inspect %s", sonde).rc == 0:
            lecteur.run("docker image rm -f %s", sonde)
        lecteur.run("rm -rf %s", SONDE_CONTEXTE)
        editeur.run("rm -rf %s", contexte)
