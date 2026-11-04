"""Interposer un proxy filtrant devant l'API Docker, et le prouver.

SIX CONTRÔLES, un par objectif de la leçon. Chacun mesure un LIVRABLE de
l'apprenant, et non un fait du système : un contrôle qui serait vrai quoi que
fasse l'apprenant ne contrôle rien, et ce lab n'en avait qu'un seul là où la
leçon enseigne six choses.

CE QUI A ÉTÉ MESURÉ, le 2026-11-03, sur la VM de ce lab (Debian 13, Docker
Engine 29.9.2), avec l'image épinglée du setup :

  - un POST d'arrêt à travers un socket monté en `:ro` rend 204 et le témoin
    passe de `running` à `exited` ; le montage affiche bien `ro` ;
  - profil `CONTAINERS=1` : 200 sur `/_ping`, `/version`, `/containers/json`,
    403 sur `/info`, `/images/json`, `/volumes`, `/networks` ;
  - l'inspection d'un conteneur TIERS livre `.Config.Env` en clair ;
  - `CONTAINERS=1 ALLOW_STOP=1` : arrêt 204, création 403 ;
  - `CONTAINERS=1 POST=1` : création d'un conteneur privilégié en 201, avec
    `privileged=true binds=[/:/hote]` ;
  - portée réseau : 000 depuis un autre réseau, 200 depuis l'hôte, 000 vers
    Internet depuis un réseau `--internal` ;
  - les trois diagnostics : 403 du proxy avec « administrative rules »,
    400 du démon sur un chemin versionné, sortie 7 de curl sur le socket.

DEUX PIÈGES DE MESURE, payés pendant l'écriture de ce fichier.

`curl -X HEAD` BLOQUE. Le serveur rend le même code qu'avec `-I`, mais curl
croit lire une réponse de GET et attend le corps annoncé par `content-length`,
qui n'arrive jamais : 8 s puis sortie 28 avec un `-m 8`, et une attente
indéfinie sans lui. Mesuré sur `/containers/json` (`content-length: 29`) et sur
`/volumes`. Sur `/_ping`, `content-length` vaut 0 et la forme ne bloque pas, ce
qui rend le piège sournois. L'ancienne version de ce test utilisait
`--request HEAD`. On écrit donc `--head`, et JAMAIS `-X HEAD`.

LE COMPTE COMPTE. `ansible` appartient au groupe `docker` sur cette machine,
donc les contrôles parlent au moteur sans `sudo`, exactement comme l'apprenant.
Un contrôle qui passerait par `sudo` mesurerait un chemin que l'apprenant
n'emprunte pas.
"""

from __future__ import annotations

import json
import shlex

import pytest

from conftest import lab_host, message

#: Les objets que l'énoncé nomme. Le setup a refusé de démarrer si l'un d'eux
#: existait déjà, donc tout objet qui les porte vient de ce lab.
PROXY = "filtre-api"
RESEAU = "reseau-filtre"
CIBLE_ARRET = "cible-1"
CIBLE_SECRET = "cible-2"
CLIENT_RO = "client-ro"

#: Le digest de l'image de proxy, celui que le setup tire. Le contrôle le vérifie
#: parce qu'un tag seul laisse le contenu changer : c'est tout le propos de
#: l'épinglage, et l'annoncer sans le vérifier serait une consigne décorative.
DIGEST_PROXY = (
    "sha256:4e5e59efd3338205561c54262581992036e5a36ccca97d487b1d4ec41f9adc58"
)
#: L'image cliente, elle aussi épinglée, dont les contrôles se servent pour
#: parler au proxy depuis le réseau interne.
CLIENT_IMAGE = (
    "curlimages/curl:8.23.0@sha256:"
    "3fb7e13e5d179a845c97d78204f3f1064d1907037f26a3ebf91710571151fd93"
)
#: Le port est celui de l'API Docker en clair, et il est FIGÉ par l'image : sa
#: configuration HAProxy porte `bind [::]:2375` en dur, et l'image ne déclare
#: aucune variable de port parmi les soixante-dix qu'elle expose. Mesuré.
PORT = 2375


@pytest.fixture
def host():
    return lab_host("docker.lab")


# ────────────────────────────── les outils ──────────────────────────────────


def _inspecter(host, genre: str, nom: str) -> dict | None:
    """Rend l'objet inspecté, ou None s'il n'existe pas.

    On distingue l'absence de l'échec : un objet absent est un travail qui n'a
    pas été fait, et son message doit le dire plutôt que de livrer une trace.
    """
    commande = {"conteneur": "inspect", "reseau": "network inspect"}[genre]
    # `docker` EN TÊTE, et c'est une correction payée : sans lui la commande
    # jouée était `inspect <nom>`, que le shell ne connaît pas, donc rc != 0,
    # donc None, donc « le conteneur n'existe pas » sur un conteneur bien
    # présent. Les sept contrôles échouaient tous pour cette seule raison, et
    # leur message accusait l'apprenant.
    resultat = host.run(shlex.join(["docker", *commande.split(), nom]))
    if resultat.rc != 0:
        return None
    charge = json.loads(resultat.stdout)
    return charge[0] if charge else None


def _requete(host, chemin: str, methode: str = "GET", entetes: bool = False,
             delai: int = 8):
    """Interroge le proxy depuis le réseau interne, et rend (code, corps).

    LE CLIENT EST JETABLE (`--rm`) et branché sur le réseau du lab : c'est la
    seule façon de joindre un proxy qui ne publie aucun port, et c'est celle que
    la leçon enseigne.

    `entetes=True` passe `--head`, et non `-X HEAD` : voir la docstring du
    module, cette seconde forme bloque jusqu'au délai.
    """
    args = [
        "docker", "run", "--rm", "--network", RESEAU, CLIENT_IMAGE,
        # LE DÉLAI SE BORNE, MAIS PAS AU HASARD. Sans borne, une forme de
        # requête qui bloque fait traîner le contrôle au lieu de le faire
        # échouer. Trop court, elle fait échouer un travail JUSTE : un arrêt de
        # conteneur attend le délai de grâce du moteur, et `sleep` ignore le
        # signal poli, donc l'arrêt prend une dizaine de secondes. Mesuré :
        # avec `-m 8`, curl abandonnait en rc 28 sur un arrêt parfaitement
        # valide, et le lab refusait un travail correct. Les lectures gardent
        # 8 s, l'arrêt en reçoit 30.
        "-m", str(delai), "-s", "-w", "\n%{http_code}",
    ]
    if entetes:
        args.append("--head")
    elif methode != "GET":
        args += ["-X", methode]
    args.append(f"http://{PROXY}:{PORT}{chemin}")
    resultat = host.run(shlex.join(args))
    lignes = resultat.stdout.rsplit("\n", 1)
    code = lignes[-1].strip() if len(lignes) > 1 else ""
    corps = lignes[0] if len(lignes) > 1 else resultat.stdout
    return code, corps


def _exiger_proxy(host) -> dict:
    proxy = _inspecter(host, "conteneur", PROXY)
    assert proxy is not None, message(
        en=f"The container `{PROXY}` does not exist: deploy the proxy first.",
        fr=f"Le conteneur `{PROXY}` n'existe pas : déployez d'abord le proxy.",
    )
    assert proxy["State"]["Running"], message(
        en=f"The container `{PROXY}` exists but is not running.",
        fr=f"Le conteneur `{PROXY}` existe mais ne tourne pas.",
    )
    return proxy


def _variables(proxy: dict) -> dict[str, str]:
    """Les variables d'environnement du proxy, en dictionnaire.

    On lit `.Config.Env` et non la ligne de commande : les variables d'un
    conteneur se fixent à sa création, et c'est l'inspection qui dit ce qui a
    réellement été posé.
    """
    paires = {}
    for entree in proxy["Config"].get("Env") or []:
        if "=" in entree:
            cle, valeur = entree.split("=", 1)
            paires[cle] = valeur
    return paires


# ───────────────────────────── les six contrôles ────────────────────────────


def test_le_socket_en_lecture_seule_n_a_pas_protege_le_temoin(host) -> None:
    """Le `:ro` protège le fichier du socket, pas les requêtes qui y passent.

    CE QUE CE CONTRÔLE MESURE, ET CE QU'IL NE PEUT PAS MESURER. Il ne peut pas
    distinguer un arrêt demandé par l'API d'un `docker stop`, et il serait
    malhonnête de le prétendre : la CLI appelle la même API, le démon ne voit
    aucune différence. Il mesure donc le DISPOSITIF, qui est le livrable : un
    client qui monte le socket en lecture seule, laissé en place, et le témoin
    tombé. C'est le montage `ro` qui porte la leçon, et il s'inspecte.
    """
    client = _inspecter(host, "conteneur", CLIENT_RO)
    assert client is not None, message(
        en=f"The container `{CLIENT_RO}` does not exist. Keep in place the "
           "client you used to send the stop request through the read-only "
           "socket: it is what proves the point.",
        fr=f"Le conteneur `{CLIENT_RO}` n'existe pas. Laissez en place le "
           "client qui a servi à envoyer l'arrêt à travers le socket en "
           "lecture seule : c'est lui qui prouve la démonstration.",
    )
    montages = [
        m for m in client.get("Mounts") or []
        if m.get("Destination") == "/var/run/docker.sock"
    ]
    assert montages, message(
        en=f"`{CLIENT_RO}` does not mount the Docker socket. Mount "
           "/var/run/docker.sock in it, read-only.",
        fr=f"`{CLIENT_RO}` ne monte pas le socket Docker. Montez-y "
           "/var/run/docker.sock en lecture seule.",
    )
    assert not montages[0].get("RW", True), message(
        en=f"`{CLIENT_RO}` mounts the socket read-WRITE. The point of this "
           "step is that read-only is already enough to stop a container: "
           "mount it with `:ro`.",
        fr=f"`{CLIENT_RO}` monte le socket en lecture-ÉCRITURE. Tout le propos "
           "de cette étape est que la lecture seule suffit déjà à arrêter un "
           "conteneur : montez-le avec `:ro`.",
    )
    temoin = _inspecter(host, "conteneur", CIBLE_ARRET)
    assert temoin is not None, message(
        en=f"The witness `{CIBLE_ARRET}` is gone. Stop it, do not remove it: "
           "its stopped state is the proof.",
        fr=f"Le témoin `{CIBLE_ARRET}` a disparu. Arrêtez-le, ne le supprimez "
           "pas : son état arrêté est la preuve.",
    )
    assert temoin["State"]["Status"] == "exited", message(
        en=f"The witness `{CIBLE_ARRET}` is still `"
           f"{temoin['State']['Status']}`. Send it a stop request through the "
           "read-only socket, and watch the daemon carry it out.",
        fr=f"Le témoin `{CIBLE_ARRET}` est encore en `"
           f"{temoin['State']['Status']}`. Envoyez-lui un ordre d'arrêt à "
           "travers le socket en lecture seule, et regardez le moteur "
           "l'exécuter.",
    )


def test_le_proxy_est_epingle_durci_et_seul_a_monter_le_socket(host) -> None:
    """Le déploiement : épinglé, durci, isolé, sans port publié.

    CINQ PROPRIÉTÉS, chacune refusable séparément, et chacune mesurée sur
    l'inspection plutôt que sur la ligne de commande : ce qui compte est ce que
    le moteur a retenu, non ce que l'apprenant croit avoir tapé.
    """
    proxy = _exiger_proxy(host)

    assert DIGEST_PROXY in (proxy["Image"] or "") or any(
        DIGEST_PROXY in ref for ref in (proxy.get("RepoDigests") or [])
    ) or DIGEST_PROXY in (proxy["Config"].get("Image") or ""), message(
        en=f"`{PROXY}` does not run the pinned image. Reuse the reference from "
           "images.env, tag AND digest: a tag alone lets the content change "
           "under you.",
        fr=f"`{PROXY}` ne tourne pas l'image épinglée. Reprenez la référence "
           "de images.env, tag ET digest : un tag seul laisse le contenu "
           "changer sous vos pieds.",
    )
    assert proxy["HostConfig"].get("ReadonlyRootfs"), message(
        en=f"`{PROXY}` does not run with a read-only root filesystem. Add "
           "`--read-only`.",
        fr=f"`{PROXY}` ne tourne pas avec une racine en lecture seule. "
           "Ajoutez `--read-only`.",
    )
    tmpfs = proxy["HostConfig"].get("Tmpfs") or {}
    assert "/run" in tmpfs, message(
        en=f"`{PROXY}` has no writable /run. With `--read-only` alone HAProxy "
           "cannot write its configuration: add `--tmpfs /run`.",
        fr=f"`{PROXY}` n'a pas de /run inscriptible. Avec `--read-only` seul, "
           "HAProxy ne peut pas écrire sa configuration : ajoutez "
           "`--tmpfs /run`.",
    )
    # DEUX CHAMPS, ET NON UN SEUL, et c'est une correction payée par la triche.
    # Mesuré le 2026-11-03 : sur un réseau `--internal`, Docker IGNORE la
    # publication de port. Un proxy lancé avec `-p 12375:2375` sur un tel réseau
    # affiche `NetworkSettings.Ports = {"2375/tcp": null}`, `docker port` ne rend
    # rien, et le port n'est pas joignable depuis l'hôte (000). Sur un réseau
    # ordinaire, le même `-p` publie pour de vrai (200).
    #
    # Lire la seule publication EFFECTIVE laissait donc passer un `-p` écrit par
    # l'apprenant : la faute n'avait aucun effet AUJOURD'HUI, mais le jour où le
    # réseau cesse d'être interne, le port s'ouvre. `HostConfig.PortBindings`
    # garde l'intention, et c'est elle qu'on refuse.
    effectifs = {
        port: liens
        for port, liens in (proxy["NetworkSettings"].get("Ports") or {}).items()
        if liens
    }
    demandes = {
        port: liens
        for port, liens in (proxy["HostConfig"].get("PortBindings") or {}).items()
        if liens
    }
    assert not effectifs, message(
        en=f"`{PROXY}` publishes {sorted(effectifs)} on the host. This proxy has "
           "neither authentication nor TLS: publish nothing, and reach it by "
           "name from its network.",
        fr=f"`{PROXY}` publie {sorted(effectifs)} sur l'hôte. Ce proxy n'a ni "
           "authentification ni TLS : ne publiez rien, et joignez-le par son "
           "nom depuis son réseau.",
    )
    assert not demandes, message(
        en=f"`{PROXY}` was started with a port publication ({sorted(demandes)}) "
           "that the internal network currently makes ineffective. Measured: "
           "`docker port` shows nothing and the port is unreachable, so the "
           "mistake is invisible today and opens the proxy the day the network "
           "stops being internal. Remove the `-p`.",
        fr=f"`{PROXY}` a été lancé avec une publication de port "
           f"({sorted(demandes)}) que le réseau interne rend pour l'instant "
           "sans effet. Mesuré : `docker port` n'affiche rien et le port est "
           "injoignable, donc la faute est invisible aujourd'hui et ouvrira le "
           "proxy le jour où le réseau cessera d'être interne. Retirez le "
           "`-p`.",
    )
    socket_monte = [
        m for m in proxy.get("Mounts") or []
        if m.get("Destination") == "/var/run/docker.sock"
    ]
    assert socket_monte, message(
        en=f"`{PROXY}` does not mount the Docker socket: it has nothing to "
           "filter.",
        fr=f"`{PROXY}` ne monte pas le socket Docker : il n'a rien à filtrer.",
    )

    # Le témoin porteur du service ne doit PAS monter le socket : le proxy est
    # le seul à le faire, et c'est ce qui donne un sens au filtrage.
    cible = _inspecter(host, "conteneur", CIBLE_SECRET)
    if cible is not None:
        fautifs = [
            m for m in cible.get("Mounts") or []
            if m.get("Destination") == "/var/run/docker.sock"
        ]
        assert not fautifs, message(
            en=f"`{CIBLE_SECRET}` still mounts the Docker socket. The proxy "
               "must be the ONLY container to mount it, otherwise it filters "
               "nothing.",
            fr=f"`{CIBLE_SECRET}` monte encore le socket Docker. Le proxy doit "
               "être le SEUL à le monter, sinon il ne filtre rien.",
        )


def test_le_profil_de_lecture_ouvre_ce_qu_il_faut_et_rien_de_plus(host) -> None:
    """La matrice du profil, et `HEAD` qui suit le même filtrage que `GET`.

    Les quatre chemins fermés appartiennent à des familles que l'énoncé ne
    demande pas d'ouvrir. Les voir en 403 prouve que le profil est étroit, et
    non que le proxy est cassé : les trois premiers répondent 200.
    """
    _exiger_proxy(host)
    for chemin in ("/_ping", "/version", "/containers/json"):
        code, _ = _requete(host, chemin)
        assert code == "200", message(
            en=f"GET {chemin} answers {code}, expected 200. The reading "
               "profile of the containers family must be open.",
            fr=f"GET {chemin} répond {code}, au lieu de 200. Le profil de "
               "lecture de la famille des conteneurs doit être ouvert.",
        )
    for chemin in ("/info", "/images/json", "/volumes", "/networks"):
        code, _ = _requete(host, chemin)
        assert code == "403", message(
            en=f"GET {chemin} answers {code}, expected 403. This family is not "
               "needed here: leave it closed, one variable opens a whole "
               "family at once.",
            fr=f"GET {chemin} répond {code}, au lieu de 403. Cette famille "
               "n'est pas nécessaire ici : laissez-la fermée, une variable "
               "ouvre une famille entière d'un coup.",
        )
    # `HEAD` suit le filtrage de `GET` : mesuré, une famille FERMÉE rend 403.
    # C'est le contrôle qui attrape un profil ouvert en grand sans le savoir.
    code, _ = _requete(host, "/volumes", entetes=True)
    assert code == "403", message(
        en=f"HEAD /volumes answers {code}, expected 403. A route open for "
           "reading also accepts HEAD, so a closed family must refuse it too.",
        fr=f"HEAD /volumes répond {code}, au lieu de 403. Une route ouverte en "
           "lecture accepte aussi HEAD, donc une famille fermée doit le "
           "refuser également.",
    )


def test_le_secret_du_temoin_ne_passe_plus_par_l_environnement(host) -> None:
    """Ce qu'un profil de LECTURE expose, et ce qu'on en tire.

    LE POINT DU CONTRÔLE. `CONTAINERS=1` ouvre l'inspection, donc `.Config.Env`
    de n'importe quel conteneur de la machine, secrets compris. Le setup a
    volontairement posé `CLE_API` avec `-e` sur le témoin. La conclusion que la
    leçon demande d'en tirer est de SORTIR le secret de l'environnement : c'est
    ce livrable qui est mesuré, et il se mesure à travers le proxy, comme un
    client le verrait.
    """
    _exiger_proxy(host)
    cible = _inspecter(host, "conteneur", CIBLE_SECRET)
    assert cible is not None, message(
        en=f"The witness `{CIBLE_SECRET}` is gone. Recreate it without its "
           "secret in the environment, keeping its name.",
        fr=f"Le témoin `{CIBLE_SECRET}` a disparu. Recréez-le sans son secret "
           "dans l'environnement, en gardant son nom.",
    )
    assert cible["State"]["Running"], message(
        en=f"`{CIBLE_SECRET}` is not running. It carries the service whose "
           "secret must stay out of reach.",
        fr=f"`{CIBLE_SECRET}` ne tourne pas. Il porte le service dont le "
           "secret doit rester hors de portée.",
    )

    # On lit ce que verrait un client du réseau interne, et non l'inspection
    # locale : c'est la vue de l'attaquant qui compte.
    code, corps = _requete(host, f"/containers/{CIBLE_SECRET}/json")
    assert code == "200", message(
        en=f"Inspecting {CIBLE_SECRET} through the proxy answers {code}. The "
           "reading profile should allow it.",
        fr=f"L'inspection de {CIBLE_SECRET} à travers le proxy répond {code}. "
           "Le profil de lecture devrait l'autoriser.",
    )
    assert "CLE_API" not in corps, message(
        en=f"The inspection of `{CIBLE_SECRET}` through the proxy still "
           "returns CLE_API in .Config.Env. A reading profile is enough to "
           "read it, from any container on the network. Pass the secret as a "
           "mounted file instead of `-e`.",
        fr=f"L'inspection de `{CIBLE_SECRET}` à travers le proxy rend encore "
           "CLE_API dans .Config.Env. Un simple profil de lecture suffit à le "
           "lire, depuis n'importe quel conteneur du réseau. Passez le secret "
           "par un fichier monté au lieu de `-e`.",
    )


def test_une_action_precise_est_ouverte_sans_donner_root_sur_l_hote(host) -> None:
    """`ALLOW_STOP` ouvre l'arrêt ; `POST=1` avec `CONTAINERS=1` ouvre l'hôte.

    POURQUOI CE CONTRÔLE N'EST PAS BLOQUANT. Ce lab est un `lab`, pas une
    épreuve : il n'évalue personne, donc un contrôle bloquant n'y aurait pas de
    sens. L'interdiction revient à l'épreuve du module, qui la reprendra. Ici,
    c'est un contrôle parmi six.

    MESURÉ : avec `CONTAINERS=1 POST=1`, une création de conteneur portant
    `Privileged` et un montage de `/` a répondu 201, et l'inspection du
    conteneur créé affichait `privileged=true binds=[/:/hote]`. C'est pourquoi
    la combinaison est refusée ici, et non parce qu'elle « fait peur ».
    """
    proxy = _exiger_proxy(host)
    variables = _variables(proxy)

    assert variables.get("CONTAINERS") == "1", message(
        en="The proxy does not carry CONTAINERS=1: the tool cannot read the "
           "containers it is supposed to watch.",
        fr="Le proxy ne porte pas CONTAINERS=1 : l'outil ne peut pas lire les "
           "conteneurs qu'il est censé surveiller.",
    )
    assert variables.get("ALLOW_STOP") == "1", message(
        en="The proxy does not carry ALLOW_STOP=1. The tool must be able to "
           "stop a container, and ALLOW_ variables open ONE action instead of "
           "a whole family.",
        fr="Le proxy ne porte pas ALLOW_STOP=1. L'outil doit pouvoir arrêter "
           "un conteneur, et les variables ALLOW_ ouvrent UNE action au lieu "
           "d'une famille entière.",
    )
    assert variables.get("POST", "0") != "1", message(
        en="The proxy carries POST=1 together with CONTAINERS=1. Measured: a "
           "client can then create a privileged container that mounts the "
           "host root, and the daemon answers 201. That combination is root "
           "on the host. Open the precise action (ALLOW_STOP) instead.",
        fr="Le proxy porte POST=1 en même temps que CONTAINERS=1. Mesuré : un "
           "client peut alors créer un conteneur privilégié qui monte la "
           "racine de l'hôte, et le moteur répond 201. Cette combinaison vaut "
           "root sur l'hôte. Ouvrez l'action précise (ALLOW_STOP) à la place.",
    )

    # LA PREUVE PAR L'USAGE : l'arrêt passe, la création est refusée. On s'en
    # prend au témoin DÉJÀ arrêté du premier contrôle, qu'on redémarre pour la
    # mesure et qui finit arrêté comme il l'était : l'état du lab est rendu
    # intact.
    host.run(shlex.join(["docker", "start", CIBLE_ARRET]))
    # `delai=30` : l'arrêt attend le délai de grâce du moteur. Voir `_requete`.
    code, _ = _requete(host, f"/containers/{CIBLE_ARRET}/stop", methode="POST",
                       delai=30)
    assert code == "204", message(
        en=f"A stop through the proxy answers {code}, expected 204. With "
           "ALLOW_STOP=1 the action must pass.",
        fr=f"Un arrêt à travers le proxy répond {code}, au lieu de 204. Avec "
           "ALLOW_STOP=1, l'action doit passer.",
    )
    code, _ = _requete(host, "/containers/create", methode="POST")
    assert code == "403", message(
        en=f"Creating a container through the proxy answers {code}, expected "
           "403. ALLOW_STOP must open the stop action WITHOUT opening "
           "creation: a client that can create chooses its own mounts and "
           "privileges.",
        fr=f"La création d'un conteneur à travers le proxy répond {code}, au "
           "lieu de 403. ALLOW_STOP doit ouvrir l'arrêt SANS ouvrir la "
           "création : un client qui peut créer choisit ses montages et ses "
           "privilèges.",
    )
    # On rend le témoin dans l'état où le premier contrôle l'attend.
    host.run(shlex.join(["docker", "stop", CIBLE_ARRET]))


def test_la_portee_du_proxy_est_bornee_par_son_reseau(host) -> None:
    """`--internal` coupe la sortie ; la séparation des réseaux fait l'isolement.

    TROIS EFFETS QUE LA LEÇON SÉPARE, et que ce contrôle mesure séparément,
    parce qu'on les attribue souvent tous les trois à `--internal` :

      - l'isolement entre conteneurs vient de la SÉPARATION DES RÉSEAUX ;
      - `--internal` coupe la sortie vers Internet ;
      - et l'hôte, lui, atteint le proxy dans les deux cas. Ce dernier point
        n'est pas un défaut à corriger : c'est une limite à connaître, donc il
        est mesuré et affirmé, non exigé.
    """
    proxy = _exiger_proxy(host)
    reseau = _inspecter(host, "reseau", RESEAU)
    assert reseau is not None, message(
        en=f"The network `{RESEAU}` does not exist.",
        fr=f"Le réseau `{RESEAU}` n'existe pas.",
    )
    assert reseau.get("Internal"), message(
        en=f"`{RESEAU}` is not internal. Create it with `--internal`: it is "
           "what denies the proxy, and its clients, any route to the "
           "Internet.",
        fr=f"`{RESEAU}` n'est pas interne. Créez-le avec `--internal` : c'est "
           "lui qui prive le proxy, et ses clients, de toute route vers "
           "Internet.",
    )
    assert RESEAU in (proxy["NetworkSettings"].get("Networks") or {}), message(
        en=f"`{PROXY}` is not attached to `{RESEAU}`.",
        fr=f"`{PROXY}` n'est pas rattaché à `{RESEAU}`.",
    )

    # La sortie vers Internet depuis le réseau interne : 000 attendu, mesuré.
    # `-m 8` borne l'essai ; sans borne, un réseau qui laisse sortir ferait
    # traîner le contrôle au lieu de le faire échouer.
    sortie = host.run(shlex.join([
        "docker", "run", "--rm", "--network", RESEAU, CLIENT_IMAGE,
        "-m", "8", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        "https://example.org",
    ]))
    assert sortie.stdout.strip() == "000", message(
        en=f"A client of `{RESEAU}` reaches the Internet "
           f"({sortie.stdout.strip()}). The network is not internal, or the "
           "client is also attached to another network.",
        fr=f"Un client de `{RESEAU}` atteint Internet "
           f"({sortie.stdout.strip()}). Le réseau n'est pas interne, ou le "
           "client est aussi rattaché à un autre réseau.",
    )

    # Et depuis un AUTRE réseau, le proxy est hors de portée : c'est la
    # séparation des réseaux qui le veut, pas `--internal`.
    adresses = [
        config.get("IPAddress")
        for config in (proxy["NetworkSettings"].get("Networks") or {}).values()
        if config.get("IPAddress")
    ]
    assert adresses, message(
        en=f"`{PROXY}` has no IP address on any network.",
        fr=f"`{PROXY}` n'a aucune adresse sur un réseau.",
    )
    depuis_ailleurs = host.run(shlex.join([
        "docker", "run", "--rm", CLIENT_IMAGE,
        "-m", "5", "-s", "-o", "/dev/null", "-w", "%{http_code}",
        f"http://{adresses[0]}:{PORT}/_ping",
    ]))
    assert depuis_ailleurs.stdout.strip() == "000", message(
        en=f"A container on the default bridge reaches the proxy at "
           f"{adresses[0]} ({depuis_ailleurs.stdout.strip()}). Keep the proxy "
           "on its own network, with no published port.",
        fr=f"Un conteneur du réseau bridge par défaut atteint le proxy en "
           f"{adresses[0]} ({depuis_ailleurs.stdout.strip()}). Gardez le proxy "
           "sur son réseau propre, sans port publié.",
    )


def test_les_trois_refus_se_distinguent_par_qui_les_prononce(host) -> None:
    """403 du proxy, 400 du démon, et un client qui n'ouvre pas le socket.

    POURQUOI CES TROIS-LÀ, ET PAS D'AUTRES. Ils appellent des gestes opposés :
    un 403 se corrige dans les variables du proxy, un 400 dans la requête, et
    un échec d'ouverture du socket dans le compte qui l'ouvre. Confondre les
    trois fait chercher au mauvais endroit, et c'est ce que ce contrôle rend
    impossible : chacun porte une signature différente.

    LE 400 PASSE PAR UN CHEMIN VERSIONNÉ, et non par une requête d'écriture mal
    formée. C'est délibéré : le profil que ce lab exige n'ouvre pas l'écriture,
    donc le 400 du démon n'y serait pas atteignable autrement. Mesuré :
    `/v1.99/containers/json` rend 400 avec « client version 1.99 is too new ».
    """
    _exiger_proxy(host)

    # a. LE PROXY refuse, et il signe son refus.
    code, corps = _requete(host, "/volumes")
    assert code == "403", message(
        en=f"GET /volumes answers {code}, expected 403 from the proxy.",
        fr=f"GET /volumes répond {code}, au lieu du 403 du proxy.",
    )
    assert "administrative rules" in corps, message(
        en="The 403 body does not carry « Request forbidden by administrative "
           f"rules ». That text is the proxy's signature; here the body was: "
           f"{corps[:200]}",
        fr="Le corps du 403 ne porte pas « Request forbidden by administrative "
           "rules ». Ce texte est la signature du proxy ; ici le corps "
           f"valait : {corps[:200]}",
    )

    # b. LE DÉMON refuse, et son message est du JSON.
    code, corps = _requete(host, "/v1.99/containers/json")
    assert code == "400", message(
        en=f"GET /v1.99/containers/json answers {code}, expected 400. A "
           "versioned path the daemon does not support goes THROUGH the proxy "
           "and is rejected by the daemon: the two refusals are not the same.",
        fr=f"GET /v1.99/containers/json répond {code}, au lieu de 400. Un "
           "chemin versionné que le moteur ne sait pas servir TRAVERSE le "
           "proxy et se fait rejeter par le moteur : les deux refus ne sont "
           "pas de même nature.",
    )
    assert "message" in corps, message(
        en=f"The 400 body is not the daemon's JSON message: {corps[:200]}",
        fr=f"Le corps du 400 n'est pas le message JSON du moteur : "
           f"{corps[:200]}",
    )

    # c. LE CLIENT n'ouvre même pas le socket, et cela ne ressemble à aucun des
    # deux : il n'y a pas de code HTTP du tout, seulement un code de sortie.
    #
    # On n'utilise PAS `--user root` ici, et c'est le propos : le socket est en
    # `root:docker 660` et l'image cliente tourne en `curl_user`. Mesuré :
    # sortie 7, « Could not connect to server ». Avec `--user root`, la même
    # requête passe en 204.
    echec = host.run(shlex.join([
        "docker", "run", "--rm",
        "-v", "/var/run/docker.sock:/var/run/docker.sock:ro", CLIENT_IMAGE,
        "--unix-socket", "/var/run/docker.sock",
        "-m", "8", "-s", "-S", "-o", "/dev/null",
        f"http://localhost/containers/{CIBLE_SECRET}/json",
    ]))
    assert echec.rc != 0, message(
        en="A client running as the image's default user managed to open the "
           "Docker socket. On this machine the socket is root:docker 0660 and "
           "the curl image runs as curl_user, so this should fail with exit 7. "
           "Check that nothing has loosened the socket's permissions.",
        fr="Un client lancé sous l'utilisateur par défaut de l'image est "
           "parvenu à ouvrir le socket Docker. Sur cette machine le socket est "
           "en root:docker 0660 et l'image curl tourne en curl_user : cela "
           "devrait échouer avec le code 7. Vérifiez que rien n'a relâché les "
           "droits du socket.",
    )
